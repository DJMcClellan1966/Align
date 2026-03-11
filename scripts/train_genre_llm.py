#!/usr/bin/env python3
"""
Train scratchLLM model on genre corpus (optional).
If corpus exists under align data/<genre>/genre_sentences.jsonl, build a corpus and run training.
Otherwise no-op (Mirror can work with truth-base only).
"""
from __future__ import annotations

import json
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
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main() -> int:
    genre_id = sys.argv[1] if len(sys.argv) > 1 else "retirement"
    paths = load_paths()
    scratchllm_path = paths.get("scratchllm_path")
    if not scratchllm_path or not Path(scratchllm_path).exists():
        print("Configure scratchllm_path in config/paths.json.", file=sys.stderr)
        return 1
    data_dir = Path(paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or ALIGN_ROOT / "data")
    genre_dir = data_dir / genre_id
    genre_sentences = genre_dir / "genre_sentences.jsonl"
    if not genre_sentences.exists():
        return 0  # no corpus; skip training
    # Build corpus dir for scratchLLM: corpus.jsonl format if needed
    corpus_dir = genre_dir / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    corpus_file = corpus_dir / "corpus.jsonl"
    count = 0
    with open(genre_sentences, encoding="utf-8") as fin:
        with open(corpus_file, "w", encoding="utf-8") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    if text:
                        fout.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
                        count += 1
                except json.JSONDecodeError:
                    pass
    if count == 0:
        return 0
    train_script = Path(scratchllm_path) / "scripts" / "train_model.py"
    if not train_script.exists():
        return 0  # scratchLLM may not have train_model; Mirror works without it
    env = os.environ.copy()
    env["PYTHONPATH"] = str(scratchllm_path) + (os.pathsep + env.get("PYTHONPATH", ""))
    r = subprocess.call(
        [sys.executable, str(train_script), str(corpus_dir), "--epochs", "2"],
        cwd=str(scratchllm_path),
        env=env,
    )
    return 0 if r == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
