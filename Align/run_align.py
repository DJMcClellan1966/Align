#!/usr/bin/env python3
"""Run Align from the repo root (parent of this Align folder)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
import run_align
run_align.main()
