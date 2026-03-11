"""
Bridge: answer from Mirror (scratchLLM truth_base) and optionally from dictionary (BasisEngine).
Concept-grounded flow: concept retrieval -> genre style sentences -> generate (retrieve) -> dictionary critic.
When ALIGN_DICTIONARY_PATH is set, explain/compare/relate-style queries use concept bundle and style retrieval.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

_align_root = Path(__file__).resolve().parent.parent


def _dict_engine():
    """Lazy-load BasisEngine from dictionary repo when available."""
    dict_path = os.environ.get("ALIGN_DICTIONARY_PATH")
    if not dict_path or not Path(dict_path).exists():
        return None
    import sys
    dict_root = Path(dict_path).resolve()
    if str(dict_root) not in sys.path:
        sys.path.insert(0, str(dict_root))
    try:
        from src.basis_engine import BasisEngine
        return BasisEngine(project_root=dict_root)
    except ImportError:
        return None


def _align_data_dir() -> Path:
    d = os.environ.get("ALIGN_DATA_DIR") or os.environ.get("ALIGN_ROOT")
    if d:
        p = Path(d)
        return p / "data" if "data" not in str(p).replace("\\", "/").split("/")[-1] else p
    return _align_root / "data"


def _build_combined_truth_base(
    mirror_path: Optional[str],
    style_sentences: list[str],
) -> Optional[str]:
    """Merge Mirror truth base + genre style sentences into a temp JSONL; return temp path for respond_formal_only."""
    lines: list[str] = []
    if mirror_path and Path(mirror_path).exists():
        try:
            with open(mirror_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        lines.append(line.rstrip())
        except OSError:
            pass
    for s in (style_sentences or []):
        if (s or "").strip():
            st = {"text": (s[:500] if len(s) > 500 else s).strip(), "tier": 2, "source": "genre", "category": "style"}
            lines.append(json.dumps(st, ensure_ascii=False))
    if not lines:
        return mirror_path
    try:
        fd, path = tempfile.mkstemp(suffix=".jsonl", prefix="align_tb_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        return path
    except Exception:
        return mirror_path


def query(
    question: str,
    truth_base_path: Optional[str] = None,
    ir_path: Optional[str] = None,
    top_k: int = 5,
    max_tier: int = 2,
    use_dictionary: bool = True,
    data_dir: Optional[Path] = None,
) -> tuple[str, str, Optional[dict[str, Any]]]:
    """
    Answer from Mirror (+ genre style) and optionally dictionary.
    Concept-grounded: retrieves concept bundle and style sentences, merges style into retrieval pool, runs dictionary critic.
    Returns (response_text, source, critic_info). critic_info has score, decision, message when dictionary available.
    """
    source = "mirror"
    response = ""
    critic_info: Optional[dict[str, Any]] = None
    engine = _dict_engine() if use_dictionary else None
    data_dir = data_dir or _align_data_dir()

    # Concept + style retrieval (when dictionary or shared_info available)
    style_sentences: list[str] = []
    concept_bundle_for_log: dict[str, Any] = {}
    if use_dictionary or True:
        try:
            from .concept_style_retrieval import retrieve as concept_retrieve, intent_to_register
            register = intent_to_register(question)
            concept_bundle_for_log, style_sentences = concept_retrieve(
                question, engine, data_dir=data_dir, genre_id="retirement", register=register
            )
        except Exception:
            pass

    tb_path = _build_combined_truth_base(truth_base_path, style_sentences)
    if tb_path or ir_path:
        try:
            from base.respond import respond_formal_only
            out = respond_formal_only(
                question,
                truth_base_path=tb_path,
                ir_path=ir_path,
                top_k=top_k,
                max_tier=max_tier,
                resolve=True,
            )
            response = (out[0] or "").strip()
            if tb_path and tb_path != truth_base_path and os.path.isfile(tb_path):
                try:
                    os.unlink(tb_path)
                except OSError:
                    pass
        except Exception:
            pass

    if use_dictionary and (not response or len(response) < 50):
        if engine is not None:
            try:
                result = engine.process(question)
                if result and getattr(result, "response", "").strip():
                    extra = result.response.strip()
                    if response:
                        response = response + "\n\n[From dictionary]\n" + extra
                        source = "mirror+dictionary"
                    else:
                        response = extra
                        source = "dictionary"
            except Exception:
                pass

    if response and engine is not None:
        try:
            from .dictionary_critic import score_and_decide
            critic_info = score_and_decide(response, engine)
            if critic_info.get("message") and critic_info.get("show_warning"):
                response = response + "\n\n" + critic_info["message"]
        except Exception:
            pass

    # Episodic trace: log (query, response, source, concepts_used)
    try:
        from .episodic import log_trace
        log_trace(
            question,
            response,
            source,
            concepts_used=concept_bundle_for_log.get("terms") or [],
            data_dir=data_dir,
        )
    except Exception:
        pass

    return (
        response or "I don't have a clear answer for that yet. Try rephrasing or adding more with Remember this.",
        source,
        critic_info,
    )
