#!/usr/bin/env python3
"""
Build an app from description using dictionary (context) and App Forge (templates).
Enriches context with Mirror profile/truth_base when available.
Optional: refine description with Mirror before build; two-phase: twin rewrites app copy (labels, tooltips).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ALIGN_ROOT / "config" / "paths.json"


def load_paths() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _slug(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[-\s]+", "-", s).strip("-") or "app"


def _shared_info_context(data_dir: Path) -> dict | None:
    """Load shared info (profile + Mirror + meds + appointments). App Forge is where this information is shared."""
    try:
        sys.path.insert(0, str(ALIGN_ROOT))
        from Align.shared_info import load_shared_info
        return load_shared_info(data_dir)
    except Exception:
        return None


def _refine_description_with_mirror(
    description: str,
    data_dir: Path,
    scratchllm_path: Path | None,
) -> tuple[str, list[str]]:
    """
    Optional step: use Mirror (truth_base) to add context to the description (refined brief + key features).
    Returns (refined_description, key_features).
    """
    refined = description.strip()
    key_features: list[str] = []
    if not scratchllm_path or not scratchllm_path.exists():
        return (refined, key_features)
    mirror_tb = data_dir / "mirror" / "truth_base.jsonl"
    if not mirror_tb.exists():
        return (refined, key_features)
    try:
        if str(scratchllm_path) not in sys.path:
            sys.path.insert(0, str(scratchllm_path))
        from base.respond import respond_formal_only
        response, _, _, _ = respond_formal_only(
            description,
            truth_base_path=str(mirror_tb),
            top_k=3,
            max_tier=2,
            resolve=True,
        )
        if (response or "").strip():
            refined = refined + "\n\nRelevant context: " + (response[:400].strip())
        shared = _shared_info_context(data_dir)
        if shared:
            concepts = shared.get("concepts") or []
            key_features = [c if isinstance(c, str) else str(c.get("name", c)) for c in concepts[:10]]
    except Exception:
        pass
    return (refined, key_features)


def _extract_text_slots(content: str) -> list[tuple[str, str]]:
    """Extract replaceable UI text (labels, placeholders, titles). Returns list of (original, original) for later rewrite."""
    slots: list[tuple[str, str]] = []
    # title="...", placeholder="...", label="...", >Label text<
    for m in re.finditer(r'(?:title|placeholder|label|alt)=["\']([^"\']{1,80})["\']', content, re.I):
        slots.append((m.group(1), m.group(1)))
    for m in re.finditer(r'>([A-Za-z][^<]{0,60})</(?:button|span|label|a)', content, re.I):
        slots.append((m.group(1), m.group(1)))
    return slots


def _rewrite_slots_with_mirror(
    content: str,
    data_dir: Path,
    mirror_tb_path: Path | None,
    scratchllm_path: Path | None,
) -> str:
    """
    Two-phase: replace extracted text slots with Mirror/genre-style alternatives when available.
    For each slot, retrieve from Mirror with the slot text; if we get a short phrase, use it; else keep original.
    """
    if not mirror_tb_path or not mirror_tb_path.exists() or not scratchllm_path:
        return content
    slots = _extract_text_slots(content)
    if not slots:
        return content
    try:
        if str(scratchllm_path) not in sys.path:
            sys.path.insert(0, str(scratchllm_path))
        from base.respond import respond_formal_only
        result = content
        for orig, _ in slots:
            try:
                resp, _, _, _ = respond_formal_only(
                    orig,
                    truth_base_path=str(mirror_tb_path),
                    top_k=1,
                    max_tier=2,
                    resolve=True,
                )
                replacement = (resp or "").strip()
                if replacement and len(replacement) < 100 and replacement != orig:
                    result = result.replace(orig, replacement, 1)
            except Exception:
                pass
        return result
    except Exception:
        return content


def main() -> int:
    description = sys.argv[1] if len(sys.argv) > 1 else ""
    refine = os.environ.get("ALIGN_REFINE_DESCRIPTION", "").lower() in ("1", "true", "yes")
    rewrite_copy = os.environ.get("ALIGN_REWRITE_APP_COPY", "").lower() in ("1", "true", "yes")
    if not description.strip():
        print("Usage: build_app.py \"<description>\"", file=sys.stderr)
        return 1
    paths = load_paths()
    dict_path = paths.get("dictionary_path")
    if not dict_path or not Path(dict_path).exists():
        print("Configure dictionary_path in config/paths.json.", file=sys.stderr)
        return 1
    dict_root = Path(dict_path).resolve()
    data_dir = Path(paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or ALIGN_ROOT / "data")
    scratchllm_path = Path(paths.get("scratchllm_path") or "") if paths.get("scratchllm_path") else None
    if refine:
        description, _ = _refine_description_with_mirror(description, data_dir, scratchllm_path)
    sys.path.insert(0, str(dict_root))
    os.chdir(dict_root)
    try:
        from src.basis_engine import BasisEngine
        from src.app_builder import AppBuilder
    except ImportError as e:
        print(f"Dictionary imports failed: {e}", file=sys.stderr)
        return 1
    engine = BasisEngine(project_root=dict_root)
    context = engine.get_context_for_description(description) or {}
    if not isinstance(context, dict):
        context = {}
    shared = _shared_info_context(data_dir)
    if shared:
        context["shared_info"] = shared
        concepts = shared.get("concepts") or []
        existing = context.get("concepts") or []
        if isinstance(existing, list):
            context = dict(context)
            context["concepts"] = list(dict.fromkeys(concepts + [c.get("name") if isinstance(c, dict) else c for c in existing]))
    app_name = getattr(engine, "_extract_app_name", lambda q: "My App")(description)
    builder = AppBuilder(
        index=engine._index,
        grammar=engine._grammar,
        data_dir=engine.data_dir,
        relation_index=getattr(engine, "_relation_index", None),
    )
    out = builder.build(description, app_name=app_name, context=context)
    if not out.get("success"):
        print(out.get("error", "Build failed"), file=sys.stderr)
        return 1
    files = out.get("files") or {}
    if not files:
        print("No files generated.", file=sys.stderr)
        return 1
    if rewrite_copy:
        mirror_tb = data_dir / "mirror" / "truth_base.jsonl"
        files = {
            name: _rewrite_slots_with_mirror(content, data_dir, mirror_tb if mirror_tb.exists() else None, scratchllm_path)
            for name, content in files.items()
        }
    slug = _slug(out.get("app_name", app_name))
    out_dir = data_dir / "builds" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        fpath = out_dir / name
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
    print(f"App written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
