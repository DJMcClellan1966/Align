#!/usr/bin/env python3
"""
Align CLI: set-genre (fetch corpus, build basis, train Mirror), build-app (generate app from description).
Requires config/paths.json with dictionary_path and scratchllm_path.
"""
import json
import os
import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent
CONFIG_PATHS = ALIGN_ROOT / "config" / "paths.json"
CONFIG_GENRES = ALIGN_ROOT / "config" / "genres.json"


def load_paths() -> dict:
    if not CONFIG_PATHS.exists():
        return {}
    try:
        with open(CONFIG_PATHS, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_genres() -> dict:
    if not CONFIG_GENRES.exists():
        return {}
    try:
        with open(CONFIG_GENRES, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def run_set_genre(genre_id: str) -> int:
    paths = load_paths()
    data_dir = Path(paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or ALIGN_ROOT / "data")
    data_dir = data_dir if isinstance(data_dir, Path) else Path(data_dir)
    scripts_dir = ALIGN_ROOT / "scripts"
    fetch_script = scripts_dir / "fetch_genre_corpus.py"
    build_script = scripts_dir / "build_genre_basis.py"
    train_script = scripts_dir / "train_genre_llm.py"
    if not fetch_script.exists():
        print("Run scripts not found. Implement fetch_genre_corpus, build_genre_basis, train_genre_llm in scripts/.", file=sys.stderr)
        return 1
    os.environ["ALIGN_DATA_DIR"] = str(data_dir)
    for name, script in [("fetch", fetch_script), ("build basis", build_script), ("train", train_script)]:
        if not script.exists():
            continue
        r = os.system(f"{sys.executable} {script} {genre_id}")
        if r != 0:
            print(f"Step {name} failed.", file=sys.stderr)
            return 1
    print(f"Genre {genre_id} ready.")
    return 0


def run_build_app(description: str) -> int:
    paths = load_paths()
    if not description.strip():
        print("Usage: cli.py build-app \"<description>\"", file=sys.stderr)
        return 1
    scripts_dir = ALIGN_ROOT / "scripts"
    build_app_script = scripts_dir / "build_app.py"
    if not build_app_script.exists():
        print("scripts/build_app.py not found.", file=sys.stderr)
        return 1
    data_dir = paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or ALIGN_ROOT / "data"
    os.environ["ALIGN_DATA_DIR"] = str(data_dir)
    r = os.system(f"{sys.executable} {build_app_script} \"{description}\"")
    return 0 if r == 0 else 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: cli.py set-genre <genre_id> | build-app \"<description>\"")
        return 0
    cmd = args[0].lower()
    if cmd == "set-genre" and len(args) >= 2:
        return run_set_genre(args[1])
    if cmd == "build-app":
        return run_build_app(args[1] if len(args) >= 2 else "")
    print("Usage: cli.py set-genre <genre_id> | build-app \"<description>\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
