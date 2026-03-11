#!/usr/bin/env python3
"""
Build dictionary unified basis with Align genre corpus (genre_sentences.jsonl).
Calls dictionary's build_unified_basis with --genre-corpus pointing to align data/<genre>/genre_sentences.jsonl.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ALIGN_ROOT / "config" / "paths.json"


def load_paths() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        import json
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main() -> int:
    genre_id = sys.argv[1] if len(sys.argv) > 1 else "retirement"
    paths = load_paths()
    data_dir = Path(paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or ALIGN_ROOT / "data")
    genre_corpus = data_dir / genre_id / "genre_sentences.jsonl"
    if not genre_corpus.exists():
        print(f"Run fetch_genre_corpus.py {genre_id} first.", file=sys.stderr)
        return 1
    dict_path = paths.get("dictionary_path")
    if not dict_path or not Path(dict_path).exists():
        print("Configure dictionary_path in config/paths.json.", file=sys.stderr)
        return 1
    dict_root = Path(dict_path).resolve()
    build_script = dict_root / "scripts" / "build_unified_basis.py"
    if not build_script.exists():
        print(f"Dictionary build script not found: {build_script}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["PYTHONPATH"] = str(dict_root) + (os.pathsep + env.get("PYTHONPATH", ""))
    r = subprocess.call(
        [sys.executable, str(build_script), "--genre-corpus", str(genre_corpus)],
        cwd=str(dict_root),
        env=env,
    )
    return 0 if r == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
