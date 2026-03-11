"""
Optional agent: proactive prompts from Mirror + profile.
Suggests next questions, reminders (e.g. "Have you added your meds?"), or hobby tips.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List

from .onboarding import load_profile, profile_path, _align_data_dir


def _mirror_has_category(data_dir: Path, category: str) -> bool:
    mirror_tb = data_dir / "mirror" / "truth_base.jsonl"
    if not mirror_tb.exists():
        return False
    try:
        with open(mirror_tb, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("category") == category or category in (obj.get("text") or "").lower():
                        return True
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return False


def suggest_prompts(data_dir: Path | None = None, limit: int = 3) -> List[str]:
    """
    Return a short list of suggested prompts (e.g. reminders, next steps) from profile and Mirror.
    """
    data_dir = data_dir or _align_data_dir()
    profile = load_profile(data_dir)
    out: List[str] = []
    if profile.get("include_meds_appointments") and not _mirror_has_category(data_dir, "medication"):
        out.append("Have you added your medications or supplements? You can say \"Remember this\" after telling me.")
    if profile.get("hobby") and not _mirror_has_category(data_dir, "hobby"):
        out.append(f"Want tips for getting started with {profile.get('hobby', 'your hobby')}? Just ask.")
    if profile.get("retirement_plan") and "retired" not in (profile.get("retirement_plan") or "").lower():
        out.append("I can help you plan steps for retirement or reconnect with hobbies when you're ready.")
    return out[:limit]


def get_proactive_message(data_dir: Path | None = None) -> str | None:
    """Return a single proactive message for the UI, or None."""
    prompts = suggest_prompts(data_dir, limit=1)
    return prompts[0] if prompts else None
