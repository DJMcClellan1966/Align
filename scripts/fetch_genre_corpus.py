#!/usr/bin/env python3
"""
Fetch or build genre sentence corpus (e.g. Harvard-style) and write genre_sentences.jsonl.
Format: one JSON object per line: {"text": "...", "source": "harvard"|"curated", "reference": "..."}.
If harvard_corpus_path or a URL is configured, fetch from there; otherwise use built-in curated sentences
for retirement/hobby so the pipeline works offline.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

# Align repo root (parent of scripts/)
ALIGN_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ALIGN_ROOT / "config" / "paths.json"


def _sentences_re() -> re.Pattern:
    return re.compile(r"[.\n]+")


def _split_sentences(text: str) -> list[str]:
    parts = _sentences_re().split(text or "")
    out = []
    for p in parts:
        s = p.strip()
        if len(s) >= 5 and any(c.isalpha() for c in s):
            out.append(s)
    return out


# Curated retirement/hobby sentences when no external corpus is available
CURATED_SENTENCES = [
    ("Retirement is a time to explore new interests and reconnect with old hobbies.", "curated", "retirement"),
    ("Many people use retirement to learn gardening, hiking, or creative hobbies.", "curated", "retirement"),
    ("Planning for retirement includes thinking about how you will spend your time.", "curated", "retirement"),
    ("Reconnecting with a hobby you used to enjoy can bring structure and joy.", "curated", "hobby"),
    ("Starting a new hobby in retirement can improve well-being and social connection.", "curated", "hobby"),
    ("Small steps build lasting habits; start with one hobby or goal at a time.", "curated", "retirement"),
    ("Balance activity and rest; schedule time for hobbies and for health.", "curated", "retirement"),
    ("Tracking appointments and medications can help you stay on top of your health.", "curated", "health"),
    ("A daily routine that includes a hobby can make retirement more fulfilling.", "curated", "retirement"),
    ("Gardening, birdwatching, and journaling are popular hobbies in retirement.", "curated", "hobby"),
]


def load_paths() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def fetch_url_to_sentences(url: str, source: str = "harvard", reference: str = "") -> list[tuple[str, str, str]]:
    """Fetch text from URL, split into sentences, return (text, source, reference) list."""
    out: list[tuple[str, str, str]] = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Align/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        return out
    for sent in _split_sentences(raw):
        if len(sent) > 10:
            out.append((sent, source, reference or url[:80]))
    return out


def write_genre_jsonl(sentences: list[tuple[str, str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for text, source, ref in sentences:
            f.write(json.dumps({"text": text, "source": source, "reference": ref}, ensure_ascii=False) + "\n")


def main() -> int:
    genre_id = sys.argv[1] if len(sys.argv) > 1 else "retirement"
    paths = load_paths()
    data_dir = Path(paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or ALIGN_ROOT / "data")
    genre_dir = data_dir / genre_id
    out_path = genre_dir / "genre_sentences.jsonl"

    sentences: list[tuple[str, str, str]] = []
    harvard_path = paths.get("harvard_corpus_path") or os.environ.get("ALIGN_HARVARD_CORPUS_PATH")
    if harvard_path and Path(harvard_path).exists():
        # Local file: expect JSONL or plain text
        p = Path(harvard_path)
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("{"):
                    try:
                        obj = json.loads(line)
                        text = obj.get("text", obj.get("sentence", ""))
                        if text:
                            sentences.append((text, obj.get("source", "harvard"), obj.get("reference", "")))
                    except json.JSONDecodeError:
                        pass
                else:
                    for s in _split_sentences(line):
                        if len(s) > 10:
                            sentences.append((s, "harvard", str(p.name)))
    elif paths.get("harvard_corpus_url"):
        url = paths["harvard_corpus_url"]
        sentences = fetch_url_to_sentences(url, source="harvard", reference=url[:80])
    if not sentences:
        sentences = [(t, s, r) for t, s, r in CURATED_SENTENCES]
    write_genre_jsonl(sentences, out_path)
    print(f"Wrote {len(sentences)} sentences to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
