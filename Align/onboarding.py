"""
Align onboarding: retirement and hobby questions.
Step 1: basic info + work/retirement. Step 2: hobby + meds preference + preview.
Collects profile and persists; used to bootstrap Mirror. Supports edit-profile flow.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

# Hobby options (align with intent_templates where possible)
HOBBY_OPTIONS = [
    "Gardening", "Hiking", "Journaling", "Yoga", "Birdwatching",
    "Home brewing", "Music production", "Reading", "Crafts", "Other",
]

def _align_data_dir() -> Path:
    d = os.environ.get("ALIGN_DATA_DIR") or os.environ.get("ALIGN_ROOT")
    if d:
        return Path(d) / "data" if "data" not in str(Path(d)).replace("\\", "/").split("/")[-1] else Path(d)
    return Path(__file__).resolve().parent.parent / "data"


def profile_path(data_dir: Optional[Path] = None) -> Path:
    data_dir = data_dir or _align_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "profile.json"


def load_profile(data_dir: Optional[Path] = None) -> dict[str, Any]:
    p = profile_path(data_dir)
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_profile(profile: dict[str, Any], data_dir: Optional[Path] = None) -> Path:
    p = profile_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    return p


def run_onboarding_ui(data_dir: Optional[Path] = None, edit_mode: bool = False) -> dict[str, Any]:
    """Show Tk dialog: Step 1 (basic + work/retirement), Step 2 (hobby + meds + preview). Return and persist profile."""
    import tkinter as tk
    from tkinter import ttk

    data_dir = data_dir or _align_data_dir()
    profile: dict[str, Any] = {}
    existing = load_profile(data_dir) if edit_mode else {}

    root = tk.Tk()
    root.title("Align — Edit profile" if edit_mode else "Align — Welcome")
    root.minsize(440, 520)
    root.geometry("480x580")

    main = ttk.Frame(root, padding=16)
    main.pack(fill=tk.BOTH, expand=True)

    step_var = tk.IntVar(value=1)
    step_label = ttk.Label(main, text="Step 1 of 2", font=("", 10, "bold"))
    step_label.pack(anchor=tk.W, pady=(0, 8))

    ttk.Label(main, text="A few questions to personalize your helper", font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 12))

    # Step 1 frame
    step1 = ttk.Frame(main)
    step1.pack(fill=tk.BOTH, expand=True)

    ttk.Label(step1, text="Name (optional):").pack(anchor=tk.W)
    name_var = tk.StringVar(value=existing.get("name") or "")
    ttk.Entry(step1, textvariable=name_var, width=42).pack(fill=tk.X, pady=(0, 8))

    ttk.Label(step1, text="Age band:").pack(anchor=tk.W)
    age_var = tk.StringVar(value=existing.get("age_band") or "50–64")
    age_combo = ttk.Combobox(step1, textvariable=age_var, values=["40–49", "50–64", "65–74", "75+"], state="readonly", width=20)
    age_combo.pack(anchor=tk.W, pady=(0, 8))

    ttk.Label(step1, text="Are you currently working?").pack(anchor=tk.W)
    working_var = tk.StringVar(value="yes" if existing.get("currently_working", True) else "no")
    f_work = ttk.Frame(step1)
    f_work.pack(anchor=tk.W, pady=(0, 8))
    ttk.Radiobutton(f_work, text="Yes", variable=working_var, value="yes").pack(side=tk.LEFT, padx=(0, 12))
    ttk.Radiobutton(f_work, text="No (retired)", variable=working_var, value="no").pack(side=tk.LEFT)

    ttk.Label(step1, text="When do you plan to retire? (or when did you retire?)").pack(anchor=tk.W)
    retire_var = tk.StringVar(value=existing.get("retirement_plan") or "Within 5 years")
    retire_combo = ttk.Combobox(
        step1, textvariable=retire_var,
        values=["Within 1 year", "Within 5 years", "5–10 years", "Already retired", "Not sure"],
        state="readonly", width=25
    )
    retire_combo.pack(anchor=tk.W, pady=(0, 12))

    # Step 2 frame
    step2 = ttk.Frame(main)
    # Hobby
    ttk.Label(step2, text="Desired hobby to learn or restart:").pack(anchor=tk.W)
    hobby_var = tk.StringVar(value=existing.get("hobby") or "")
    hobby_combo = ttk.Combobox(step2, textvariable=hobby_var, values=HOBBY_OPTIONS, width=22)
    hobby_combo.pack(anchor=tk.W, pady=(0, 8))
    ttk.Label(step2, text="(Choose one or type your own)", font=("", 8), foreground="gray").pack(anchor=tk.W, pady=(0, 8))

    ttk.Label(step2, text="Include help with appointments or medications?").pack(anchor=tk.W)
    meds_var = tk.StringVar(value="yes" if existing.get("include_meds_appointments") else "no")
    f_meds = ttk.Frame(step2)
    f_meds.pack(anchor=tk.W, pady=(0, 12))
    ttk.Radiobutton(f_meds, text="Yes", variable=meds_var, value="yes").pack(side=tk.LEFT, padx=(0, 12))
    ttk.Radiobutton(f_meds, text="No", variable=meds_var, value="no").pack(side=tk.LEFT)

    preview_var = tk.StringVar(value="")
    preview_label = ttk.Label(step2, textvariable=preview_var, font=("", 9), foreground="green")
    preview_label.pack(anchor=tk.W, pady=(12, 0))

    result: list[dict] = []

    def make_profile() -> dict:
        p = {}
        p["name"] = name_var.get().strip() or None
        p["age_band"] = age_var.get().strip() or "50–64"
        p["currently_working"] = working_var.get().strip() == "yes"
        p["retirement_plan"] = retire_var.get().strip() or "Not sure"
        h = hobby_var.get().strip()
        p["hobby"] = h if h else None
        p["include_meds_appointments"] = meds_var.get().strip() == "yes"
        return p

    def update_preview() -> None:
        p = make_profile()
        parts = []
        if p.get("hobby"):
            parts.append(p["hobby"])
        parts.append(p.get("retirement_plan", ""))
        if p.get("include_meds_appointments"):
            parts.append("meds & appointments")
        preview_var.set("We'll focus on: " + ", ".join(parts) if parts else "")

    def show_step(step: int) -> None:
        step_var.set(step)
        step_label.config(text=f"Step {step} of 2")
        if step == 1:
            step2.pack_forget()
            step1.pack(fill=tk.BOTH, expand=True)
            btn_back.pack_forget()
        else:
            step1.pack_forget()
            step2.pack(fill=tk.BOTH, expand=True)
            btn_back.pack(side=tk.LEFT, padx=(0, 8))
            update_preview()

    def submit() -> None:
        profile.clear()
        profile.update(make_profile())
        save_profile(profile, data_dir)
        result.append(profile)
        root.quit()
        root.destroy()

    btn_frame = ttk.Frame(main)
    btn_frame.pack(fill=tk.X, pady=(16, 0))
    btn_back = ttk.Button(btn_frame, text="Back", command=lambda: show_step(1))
    ttk.Button(btn_frame, text="Next", command=lambda: show_step(2)).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_frame, text="Continue" if edit_mode else "Finish", command=submit).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_frame, text="Skip", command=lambda: (result.append({}), root.quit(), root.destroy())).pack(side=tk.LEFT)

    show_step(1)
    root.mainloop()
    return result[0] if result else {}


def sync_mirror_to_scratchllm(scratchllm_path: Path, data_dir: Optional[Path] = None) -> Optional[str]:
    """Copy align data/mirror to scratchLLM corpus/user_helpers/align_mirror. Returns truth_base path there."""
    data_dir = data_dir or _align_data_dir()
    mirror_src = data_dir / "mirror"
    truth_src = mirror_src / "truth_base.jsonl"
    if not truth_src.exists():
        return None
    helpers = scratchllm_path / "corpus" / "user_helpers"
    helpers.mkdir(parents=True, exist_ok=True)
    dest_dir = helpers / "align_mirror"
    dest_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    for name in ["truth_base.jsonl", "meta.json"]:
        src = mirror_src / name
        if src.exists():
            shutil.copy2(src, dest_dir / name)
    return str(dest_dir / "truth_base.jsonl")


def bootstrap_mirror_from_profile(profile: dict[str, Any], data_dir: Optional[Path] = None) -> Optional[str]:
    """Create initial Mirror corpus from profile. Updates shared_info. Returns path to truth_base.jsonl."""
    data_dir = data_dir or _align_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    mirror_dir = data_dir / "mirror"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    truth_path = mirror_dir / "truth_base.jsonl"
    statements: list[dict] = []
    if profile.get("name"):
        statements.append({"text": f"User's name (optional): {profile['name']}.", "tier": 2, "source": "profile", "category": "retirement"})
    statements.append({"text": f"Age band: {profile.get('age_band', '50–64')}.", "tier": 2, "source": "profile", "category": "retirement"})
    statements.append({"text": f"Currently working: {profile.get('currently_working', True)}.", "tier": 1, "source": "profile", "category": "retirement"})
    statements.append({"text": f"Retirement: {profile.get('retirement_plan', 'Not sure')}.", "tier": 1, "source": "profile", "category": "retirement"})
    if profile.get("hobby"):
        statements.append({"text": f"Desired hobby to learn or restart: {profile['hobby']}.", "tier": 1, "source": "profile", "category": "hobby"})
    if profile.get("include_meds_appointments"):
        statements.append({"text": "User wants help with appointments and medications.", "tier": 2, "source": "profile", "category": "health"})
    if not statements:
        return None
    with open(truth_path, "w", encoding="utf-8") as f:
        for s in statements:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    meta_path = mirror_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"source": "align_onboarding", "profile": profile}, f, indent=2, ensure_ascii=False)
    try:
        from .shared_info import refresh_shared_info
        refresh_shared_info(data_dir)
    except Exception:
        pass
    return str(truth_path)
