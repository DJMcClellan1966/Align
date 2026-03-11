#!/usr/bin/env python3
"""
Build scratchLLM corpus (corpus.jsonl + manifest.json) from genre_sentences.jsonl,
then invoke scratchLLM's train_model.py. Checkpoints go to data/<genre>/corpus/checkpoints/.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent.parent


def _load_paths() -> dict:
    path_file = ALIGN_ROOT / "config" / "paths.json"
    if not path_file.exists():
        return {}
    with open(path_file, encoding="utf-8") as f:
        return json.load(f)


def train_genre_llm(
    genre_id: str,
    align_root: Path | None = None,
    data_dir: Path | None = None,
    scratchllm_path: Path | None = None,
    epochs: int | None = None,
) -> Path:
    """
    Write data/<genre>/corpus/corpus.jsonl and manifest.json from genre_sentences.jsonl,
    then run scratchLLM train_model. Returns path to corpus directory.
    """
    align_root = align_root or ALIGN_ROOT
    paths = _load_paths()
    data_dir = data_dir or Path(paths.get("align_data_dir") or align_root / "data")
    scratch_path = scratchllm_path or Path(paths.get("scratchllm_path", ""))
    if not scratch_path or not Path(scratch_path).exists():
        raise FileNotFoundError(
            "Set config/paths.json 'scratchllm_path' to the scratchLLM repo root"
        )
    scratch_path = Path(scratch_path)

    genre_data = data_dir / genre_id
    genre_sentences = genre_data / "genre_sentences.jsonl"
    if not genre_sentences.exists():
        raise FileNotFoundError(
            f"Run fetch_genre_corpus first: {genre_sentences} not found"
        )

    corpus_dir = genre_data / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    corpus_jsonl = corpus_dir / "corpus.jsonl"
    manifest_path = corpus_dir / "manifest.json"

    n_docs = 0
    n_chars = 0
    with open(genre_sentences, encoding="utf-8") as fin, open(corpus_jsonl, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get("text", "")
                source = obj.get("source", "genre_corpus")
                ref = obj.get("reference", "")
                if not text:
                    continue
                doc = {"text": text, "source": source, "meta": {"reference": ref}}
                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
                n_docs += 1
                n_chars += len(text)
            except json.JSONDecodeError:
                continue

    n_tokens_actual = max(1, n_chars // 4)
    manifest = {
        "n_docs": n_docs,
        "n_chars": n_chars,
        "n_tokens_actual": n_tokens_actual,
        "n_tokens_inferred": 0,
        "paths_used": {"genre_sentences": str(genre_sentences)},
        "scaling_inputs": {},
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Wrote {n_docs} docs to {corpus_jsonl}, manifest to {manifest_path}", file=sys.stderr)

    # Run scratchLLM train_model.py
    train_script = scratch_path / "scripts" / "train_model.py"
    if not train_script.exists():
        raise FileNotFoundError(f"scratchLLM train script not found: {train_script}")
    cmd = [sys.executable, str(train_script), str(corpus_dir)]
    if epochs is not None:
        cmd.extend(["--epochs", str(epochs)])
    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True, cwd=str(scratch_path))
    return corpus_dir


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Build corpus from genre sentences and train scratchLLM")
    ap.add_argument("genre", help="Genre id (e.g. hobbies, art)")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--scratchllm-path", type=Path, default=None)
    ap.add_argument("--epochs", type=int, default=None, help="Training epochs (default from scratchLLM scale)")
    args = ap.parse_args()
    train_genre_llm(
        args.genre,
        data_dir=args.data_dir,
        scratchllm_path=args.scratchllm_path,
        epochs=args.epochs,
    )


if __name__ == "__main__":
    main()
