#!/usr/bin/env python3
"""
Align CLI: set-genre (fetch + build basis + train LM), build-app (build app from description).
Run from the align project root.
"""
from __future__ import annotations

import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent


def cmd_set_genre(genre_id: str, max_sentences: int = 50_000) -> None:
    """Run fetch_genre_corpus, build_genre_basis, train_genre_llm for the given genre."""
    sys.path.insert(0, str(ALIGN_ROOT))
    from scripts.fetch_genre_corpus import fetch_genre_corpus
    from scripts.build_genre_basis import build_genre_basis
    from scripts.train_genre_llm import train_genre_llm

    print(f"Fetching corpus for genre: {genre_id}", file=sys.stderr)
    fetch_genre_corpus(genre_id, max_sentences=max_sentences)
    print(f"Building unified basis for: {genre_id}", file=sys.stderr)
    build_genre_basis(genre_id)
    print(f"Training scratchLLM for: {genre_id}", file=sys.stderr)
    train_genre_llm(genre_id)
    print(f"Genre '{genre_id}' is ready.", file=sys.stderr)


def cmd_build_app(genre_id: str, description: str, output_dir: Path, app_name: str | None = None) -> None:
    """Build an app from description using the genre's basis; write to output_dir."""
    sys.path.insert(0, str(ALIGN_ROOT))
    from scripts.build_app import build_app

    result = build_app(genre_id, description, output_dir, app_name=app_name)
    if not result.get("success"):
        print(result.get("error", "Build failed"), file=sys.stderr)
        sys.exit(1)
    print(f"App written to: {result.get('output_dir')}", file=sys.stderr)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Align: genre-specific sentence dictionary + scratchLLM + app build")
    sub = ap.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set-genre", help="Set genre: fetch corpus, build basis, train LM")
    p_set.add_argument("genre", help="Genre id (e.g. hobbies, art, fiction)")
    p_set.add_argument("--max-sentences", type=int, default=50_000, help="Cap sentences to fetch (default 50000)")

    p_build = sub.add_parser("build-app", help="Build app from description (uses current genre basis)")
    p_build.add_argument("genre", help="Genre id (e.g. hobbies, art)")
    p_build.add_argument("description", help="App description (e.g. 'a recipe manager')")
    p_build.add_argument("-o", "--output-dir", type=Path, default=Path("."), help="Output directory for app files")
    p_build.add_argument("--app-name", type=str, default=None, help="App name")

    args = ap.parse_args()
    if args.command == "set-genre":
        cmd_set_genre(args.genre, max_sentences=args.max_sentences)
    elif args.command == "build-app":
        cmd_build_app(args.genre, args.description, args.output_dir, app_name=args.app_name)


if __name__ == "__main__":
    main()
