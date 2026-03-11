#!/usr/bin/env python3
"""
Build genre-aware unified basis (sentence dictionary + word-graph) by calling
the dictionary app's build with genre_corpus_path and vocabulary extension.
Writes to data/<genre>/unified_basis/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Align project root
ALIGN_ROOT = Path(__file__).resolve().parent.parent


def _load_paths() -> dict:
    path_file = ALIGN_ROOT / "config" / "paths.json"
    if not path_file.exists():
        return {}
    with open(path_file, encoding="utf-8") as f:
        return json.load(f)


def build_genre_basis(
    genre_id: str,
    align_root: Path | None = None,
    data_dir: Path | None = None,
    dictionary_path: Path | None = None,
    use_bible: bool = True,
    use_coding: bool = True,
    use_code_corpus: bool = True,
) -> Path:
    """
    Load dictionary from dictionary repo, then run dictionary's build_unified_basis
    with data_dir = align data/<genre> and genre_corpus_path = genre_sentences.jsonl.
    Returns path to unified_basis directory.
    """
    align_root = align_root or ALIGN_ROOT
    paths = _load_paths()
    data_dir = data_dir or Path(paths.get("align_data_dir") or align_root / "data")
    dict_path = dictionary_path or Path(paths.get("dictionary_path", ""))
    if not dict_path or not Path(dict_path).exists():
        raise FileNotFoundError(
            "Set config/paths.json 'dictionary_path' to the dictionary repo root (e.g. .../dictionary/dictionary)"
        )
    dict_path = Path(dict_path)

    genre_data = data_dir / genre_id
    genre_sentences = genre_data / "genre_sentences.jsonl"
    if not genre_sentences.exists():
        raise FileNotFoundError(
            f"Run fetch_genre_corpus first: {genre_sentences} not found"
        )

    # Add dictionary repo root to path so "from src.basis_layers.build import ..." and internal imports work
    if str(dict_path) not in sys.path:
        sys.path.insert(0, str(dict_path))

    # Load coding_dictionary.json from dictionary repo
    dict_json = dict_path / "src" / "coding_dictionary.json"
    if not dict_json.exists():
        dict_json = dict_path / "coding_dictionary.json"
    if not dict_json.exists():
        raise FileNotFoundError(f"Dictionary not found at {dict_path}/src/coding_dictionary.json")
    with open(dict_json, encoding="utf-8") as f:
        dictionary = json.load(f)

    from src.basis_layers.build import build_unified_basis

    def report(msg: str) -> None:
        print(msg, file=sys.stderr)

    unified_dir = build_unified_basis(
        dictionary,
        genre_data,
        report=report,
        build_vectors=False,
        use_bible=use_bible,
        use_coding=use_coding,
        use_code_corpus=use_code_corpus,
        genre_corpus_path=genre_sentences,
        extend_vocabulary_from_corpus=True,
    )
    print(f"Unified basis written to {unified_dir}", file=sys.stderr)
    return unified_dir


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Build genre unified basis (sentence dict + word-graph)")
    ap.add_argument("genre", help="Genre id (e.g. hobbies, art)")
    ap.add_argument("--data-dir", type=Path, default=None, help="Override data directory")
    ap.add_argument("--dictionary-path", type=Path, default=None, help="Override dictionary repo path")
    ap.add_argument("--no-bible", action="store_true", help="Exclude Bible from sentence index")
    ap.add_argument("--no-coding", action="store_true", help="Exclude coding sources from sentence index")
    ap.add_argument("--no-code-corpus", action="store_true", help="Exclude code_cookbook/code_complete")
    args = ap.parse_args()
    build_genre_basis(
        args.genre,
        data_dir=args.data_dir,
        dictionary_path=args.dictionary_path,
        use_bible=not args.no_bible,
        use_coding=not args.no_coding,
        use_code_corpus=not args.no_code_corpus,
    )


if __name__ == "__main__":
    main()
