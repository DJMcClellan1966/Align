#!/usr/bin/env python3
"""
Fetch genre corpus (Harvard or custom) and write genre_sentences.jsonl.
Uses config/genres.json and config/paths.json. Caps sentence count per genre.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Align project root (parent of scripts/)
ALIGN_ROOT = Path(__file__).resolve().parent.parent


def _load_config() -> tuple[dict, dict]:
    """Load genres.json and paths.json from config/."""
    config_dir = ALIGN_ROOT / "config"
    with open(config_dir / "genres.json", encoding="utf-8") as f:
        genres = json.load(f)
    path_file = config_dir / "paths.json"
    paths = {}
    if path_file.exists():
        with open(path_file, encoding="utf-8") as f:
            paths = json.load(f)
    return genres, paths


def _sentence_split(text: str) -> list[str]:
    """Split text into sentences (simple period/newline)."""
    if not text or not text.strip():
        return []
    # Normalize whitespace, split on sentence boundaries
    text = " ".join(text.split())
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) >= 5 and any(c.isalpha() for c in p):
            out.append(p)
    return out


def _fetch_harvard(
    genre_id: str,
    genre_config: dict,
    paths_config: dict,
    out_path: Path,
    max_sentences: int,
) -> int:
    """
    Load Harvard corpus from local path. User must download from
    https://huggingface.co/datasets/institutional/institutional-books-1.0
    and set paths_config["harvard_corpus_path"] to the extracted directory.
    """
    harvard_path = paths_config.get("harvard_corpus_path")
    if not harvard_path:
        # Fallback: check for data/harvard_sample or similar
        sample = ALIGN_ROOT / "data" / "harvard_sample"
        if sample.exists() and sample.is_dir():
            harvard_path = str(sample)
        else:
            raise FileNotFoundError(
                "Set config/paths.json 'harvard_corpus_path' to the directory containing "
                "Harvard/Institutional Books text files, or add sample files under data/harvard_sample/"
            )
    root = Path(harvard_path)
    if not root.is_dir():
        raise FileNotFoundError(f"harvard_corpus_path is not a directory: {root}")

    slice_name = genre_config.get("harvard_slice", "fiction")
    # If corpus has subdirs like fiction/, non_fiction/, use them
    slice_dir = root / slice_name if (root / slice_name).is_dir() else root

    collected: list[tuple[str, str, str]] = []
    for ext in ("*.txt", "*.text"):
        for fpath in slice_dir.rglob(ext):
            if len(collected) >= max_sentences:
                break
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    raw = f.read()
            except Exception:
                continue
            ref = fpath.relative_to(root) if root in fpath.parents else fpath.name
            for sent in _sentence_split(raw):
                if len(collected) >= max_sentences:
                    break
                collected.append((sent, f"harvard_{slice_name}", str(ref)))
        if len(collected) >= max_sentences:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for text, source, ref in collected:
            f.write(json.dumps({"text": text, "source": source, "reference": ref}, ensure_ascii=False) + "\n")
    return len(collected)


def _fetch_custom(
    genre_id: str,
    genre_config: dict,
    out_path: Path,
    max_sentences: int,
) -> int:
    """Load custom corpus from genre_config['path'] (JSONL or directory of text files)."""
    path = genre_config.get("path")
    if not path:
        raise ValueError(f"Genre '{genre_id}' has dataset 'custom' but no 'path' in config/genres.json")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Custom corpus path does not exist: {p}")

    collected: list[tuple[str, str, str]] = []
    if p.is_file() and p.suffix.lower() in (".jsonl", ".jsonl.gz"):
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if len(collected) >= max_sentences:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("text", obj.get("sentence", ""))
                    if not text:
                        continue
                    source = obj.get("source", "custom")
                    ref = obj.get("reference", "")
                    collected.append((text, source, ref))
                except json.JSONDecodeError:
                    continue
    elif p.is_dir():
        for fpath in p.rglob("*.txt"):
            if len(collected) >= max_sentences:
                break
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    raw = f.read()
            except Exception:
                continue
            ref = fpath.name
            for sent in _sentence_split(raw):
                if len(collected) >= max_sentences:
                    break
                collected.append((sent, "custom", ref))
    else:
        raise ValueError(f"Custom path must be a .jsonl file or a directory: {p}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for text, source, ref in collected:
            f.write(json.dumps({"text": text, "source": source, "reference": ref}, ensure_ascii=False) + "\n")
    return len(collected)


def fetch_genre_corpus(
    genre_id: str,
    align_root: Path | None = None,
    max_sentences: int = 50_000,
    data_dir: Path | None = None,
) -> Path:
    """
    Fetch corpus for genre_id and write data/<genre_id>/genre_sentences.jsonl.
    Returns path to the written file.
    """
    align_root = align_root or ALIGN_ROOT
    genres, paths = _load_config()
    if genre_id not in genres:
        raise ValueError(f"Unknown genre: {genre_id}. Known: {list(genres.keys())}")

    data_dir = data_dir or (Path(paths.get("align_data_dir") or align_root / "data"))
    out_path = data_dir / genre_id / "genre_sentences.jsonl"

    genre_config = genres[genre_id]
    dataset = genre_config.get("dataset", "harvard")

    if dataset == "harvard":
        count = _fetch_harvard(genre_id, genre_config, paths, out_path, max_sentences)
    elif dataset == "custom":
        count = _fetch_custom(genre_id, genre_config, out_path, max_sentences)
    else:
        raise ValueError(f"Unsupported dataset for genre '{genre_id}': {dataset}")

    print(f"Wrote {count} sentences to {out_path}", file=sys.stderr)
    return out_path


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Fetch genre corpus into data/<genre>/genre_sentences.jsonl")
    ap.add_argument("genre", help="Genre id (e.g. hobbies, art, fiction)")
    ap.add_argument("--max-sentences", type=int, default=50_000, help="Cap sentence count (default 50000)")
    ap.add_argument("--data-dir", type=Path, default=None, help="Override data directory")
    args = ap.parse_args()
    fetch_genre_corpus(args.genre, max_sentences=args.max_sentences, data_dir=args.data_dir)


if __name__ == "__main__":
    main()
