#!/usr/bin/env python3
"""
Load BasisEngine from genre's unified_basis, get context for description,
build app via dictionary's AppBuilder, and write output to a local folder.
All local; no cloud.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent.parent


def _load_paths() -> dict:
    path_file = ALIGN_ROOT / "config" / "paths.json"
    if not path_file.exists():
        return {}
    with open(path_file, encoding="utf-8") as f:
        return json.load(f)


def build_app(
    genre_id: str,
    description: str,
    output_dir: Path,
    app_name: str | None = None,
    align_root: Path | None = None,
    data_dir: Path | None = None,
    dictionary_path: Path | None = None,
) -> dict:
    """
    Load dictionary BasisEngine from data/<genre>/unified_basis, build app
    from description using get_context_for_description + AppBuilder, write
    files to output_dir. Returns result dict (success, app_name, files, error).
    """
    align_root = align_root or ALIGN_ROOT
    paths = _load_paths()
    data_dir = data_dir or Path(paths.get("align_data_dir") or align_root / "data")
    dict_path = dictionary_path or Path(paths.get("dictionary_path", ""))
    if not dict_path or not Path(dict_path).exists():
        return {"success": False, "error": "Set config/paths.json 'dictionary_path' to the dictionary repo root"}
    dict_path = Path(dict_path)

    genre_data = data_dir / genre_id
    unified_dir = genre_data / "unified_basis"
    if not unified_dir.exists() or not (unified_dir / "global_vocabulary.json").exists():
        return {"success": False, "error": f"Unified basis not found for genre '{genre_id}'. Run build_genre_basis first."}

    if str(dict_path) not in sys.path:
        sys.path.insert(0, str(dict_path))

    from src.basis_engine import BasisEngine
    from src.basis_tools import tool_build_app

    engine = BasisEngine(data_dir=genre_data, project_root=dict_path)
    out = tool_build_app(engine, description, app_name=app_name)

    if not out.get("success"):
        return out

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = out.get("files", {})
    for rel_path, content in files.items():
        if not rel_path or content is None:
            continue
        fpath = output_dir / rel_path
        fpath.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            fpath.write_text(content, encoding="utf-8")
        else:
            fpath.write_bytes(content)

    out["output_dir"] = str(output_dir)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Build app from description using genre basis (local)")
    ap.add_argument("genre", help="Genre id (e.g. hobbies, art)")
    ap.add_argument("description", help="App description (e.g. 'a recipe manager')")
    ap.add_argument("-o", "--output-dir", type=Path, default=Path("."), help="Directory to write app files (default: current)")
    ap.add_argument("--app-name", type=str, default=None, help="App name (default: derived from description)")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--dictionary-path", type=Path, default=None)
    args = ap.parse_args()
    result = build_app(
        args.genre,
        args.description,
        args.output_dir,
        app_name=args.app_name,
        data_dir=args.data_dir,
        dictionary_path=args.dictionary_path,
    )
    if result.get("success"):
        print(f"Built: {result.get('app_name')} -> {result.get('output_dir')}", file=sys.stderr)
    else:
        print(f"Build failed: {result.get('error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
