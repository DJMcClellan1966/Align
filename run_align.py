#!/usr/bin/env python3
"""
Launch Align: retirement and hobby helper with Mirror (LLM-twin).
Uses the Align GUI (onboarding, agent, respond_bridge, Build app with shared_info, meds/appointments, train).
"""
import json
import os
import sys
from pathlib import Path

ALIGN_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ALIGN_ROOT / "config" / "paths.json"

if str(ALIGN_ROOT) not in sys.path:
    sys.path.insert(0, str(ALIGN_ROOT))


def load_paths() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def main() -> None:
    paths = load_paths()
    scratchllm_path = paths.get("scratchllm_path") or os.environ.get("ALIGN_SCRATCHLLM_PATH")
    if scratchllm_path and Path(scratchllm_path).exists():
        sys.path.insert(0, str(Path(scratchllm_path).resolve()))
    align_data = paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or str(ALIGN_ROOT / "data")
    os.environ["ALIGN_DATA_DIR"] = str(Path(align_data).resolve())
    os.environ["ALIGN_ROOT"] = str(ALIGN_ROOT)
    os.environ["ALIGN_MODE"] = "1"
    if paths.get("dictionary_path"):
        os.environ["ALIGN_DICTIONARY_PATH"] = str(Path(paths["dictionary_path"]).resolve())

    from Align.gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
