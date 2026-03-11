"""
Shared information store: profile + Mirror summary + meds + appointments.
App Forge reads this when building apps so generated apps are the place where information is shared.
Refresh from profile and Mirror (and meds/appointments) whenever profile or Mirror changes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from .onboarding import _align_data_dir, load_profile


def shared_info_path(data_dir: Optional[Path] = None) -> Path:
    data_dir = data_dir or _align_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "shared_info.json"


def _load_mirror_statements(data_dir: Path) -> list[dict]:
    mirror_tb = data_dir / "mirror" / "truth_base.jsonl"
    if not mirror_tb.exists():
        return []
    out = []
    try:
        with open(mirror_tb, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return out


def _load_meds(data_dir: Path) -> list[dict]:
    p = data_dir / "mirror" / "meds.json"
    if not p.exists():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("meds", [])
    except (json.JSONDecodeError, OSError):
        return []


def _load_appointments(data_dir: Path) -> list[dict]:
    p = data_dir / "mirror" / "appointments.json"
    if not p.exists():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else data.get("appointments", [])
    except (json.JSONDecodeError, OSError):
        return []


def refresh_shared_info(data_dir: Optional[Path] = None) -> dict[str, Any]:
    """
    Build shared_info from profile + Mirror + meds + appointments.
    This is the single source passed to App Forge so generated apps are where information is shared.
    """
    data_dir = data_dir or _align_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    profile = load_profile(data_dir)
    statements = _load_mirror_statements(data_dir)
    meds = _load_meds(data_dir)
    appointments = _load_appointments(data_dir)
    summary_lines = [s.get("text", "") for s in statements if s.get("text")][:50]
    shared = {
        "profile": profile,
        "mirror_summary": summary_lines,
        "meds": meds,
        "appointments": appointments,
        "concepts": _concepts_from_profile_and_mirror(profile, statements, meds, appointments),
    }
    path = shared_info_path(data_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(shared, f, indent=2, ensure_ascii=False)
    return shared


def _concepts_from_profile_and_mirror(
    profile: dict, statements: list[dict], meds: list, appointments: list
) -> list[str]:
    concepts = []
    if profile.get("hobby"):
        concepts.append(profile["hobby"].strip())
    concepts.extend(["retirement", "hobby"])
    if profile.get("include_meds_appointments") or meds or appointments:
        concepts.extend(["medication", "appointment"])
    for s in statements:
        text = (s.get("text") or "").lower()
        if "med" in text or "medication" in text:
            concepts.append("medication")
        if "appointment" in text:
            concepts.append("appointment")
    return list(dict.fromkeys(concepts))


def load_shared_info(data_dir: Optional[Path] = None) -> dict[str, Any]:
    """Load shared_info; if missing or stale, refresh from profile + Mirror."""
    data_dir = data_dir or _align_data_dir()
    path = shared_info_path(data_dir)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return refresh_shared_info(data_dir)


def save_meds(meds: list[dict], data_dir: Optional[Path] = None) -> Path:
    data_dir = data_dir or _align_data_dir()
    mirror_dir = data_dir / "mirror"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    path = mirror_dir / "meds.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"meds": meds}, f, indent=2, ensure_ascii=False)
    refresh_shared_info(data_dir)
    return path


def save_appointments(appointments: list[dict], data_dir: Optional[Path] = None) -> Path:
    data_dir = data_dir or _align_data_dir()
    mirror_dir = data_dir / "mirror"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    path = mirror_dir / "appointments.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"appointments": appointments}, f, indent=2, ensure_ascii=False)
    refresh_shared_info(data_dir)
    return path
