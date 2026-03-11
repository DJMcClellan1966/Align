"""
Align GUI: retirement and hobby helper with Mirror.
Surfaces agent, uses respond_bridge (Mirror + dictionary), Edit profile, Build app (with shared_info), meds/appointments, error handling, optional train.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

def _align_data_dir() -> Path:
    d = os.environ.get("ALIGN_DATA_DIR") or os.environ.get("ALIGN_ROOT")
    if d:
        return Path(d) / "data" if "data" not in str(Path(d)).replace("\\", "/").split("/")[-1] else Path(d)
    return Path(__file__).resolve().parent.parent / "data"


def _load_paths() -> dict:
    root = Path(__file__).resolve().parent.parent
    p = root / "config" / "paths.json"
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _mirror_truth_base_path() -> Optional[str]:
    tb = _align_data_dir() / "mirror" / "truth_base.jsonl"
    return str(tb) if tb.exists() else None


def _append_to_mirror(text: str, category: str = "user", tier: int = 2) -> None:
    data_dir = _align_data_dir()
    mirror_dir = data_dir / "mirror"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    tb = mirror_dir / "truth_base.jsonl"
    line = json.dumps({"text": text[:500], "tier": tier, "source": "user", "category": category}, ensure_ascii=False) + "\n"
    with open(tb, "a", encoding="utf-8") as f:
        f.write(line)
    try:
        from .shared_info import refresh_shared_info
        refresh_shared_info(data_dir)
    except Exception:
        pass


def run_paths_dialog() -> bool:
    """Show dialog to set dictionary_path and scratchllm_path; save to config. Returns True if saved."""
    import tkinter as tk
    from tkinter import ttk

    root = Path(__file__).resolve().parent.parent
    config_path = root / "config" / "paths.json"
    paths = _load_paths()

    win = tk.Toplevel()
    win.title("Align — Paths")
    win.geometry("520x200")
    f = ttk.Frame(win, padding=16)
    f.pack(fill=tk.BOTH, expand=True)
    ttk.Label(f, text="Set paths (required for full features):", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 8))
    ttk.Label(f, text="Dictionary repo (e.g. .../dictionary/dictionary):").pack(anchor=tk.W)
    dict_var = tk.StringVar(value=paths.get("dictionary_path") or "")
    ttk.Entry(f, textvariable=dict_var, width=60).pack(fill=tk.X, pady=(0, 8))
    ttk.Label(f, text="scratchLLM repo (e.g. .../scratchLLM/scratchLLM):").pack(anchor=tk.W)
    scratch_var = tk.StringVar(value=paths.get("scratchllm_path") or "")
    ttk.Entry(f, textvariable=scratch_var, width=60).pack(fill=tk.X, pady=(0, 8))

    saved = [False]

    def save() -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = _load_paths()
        data["dictionary_path"] = dict_var.get().strip() or None
        data["scratchllm_path"] = scratch_var.get().strip() or None
        with open(config_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        saved[0] = True
        win.destroy()

    ttk.Button(f, text="Save", command=save).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(f, text="Cancel", command=win.destroy).pack(side=tk.LEFT)
    win.wait_window()
    return saved[0]


def main() -> None:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox

    root_path = Path(__file__).resolve().parent.parent
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

    paths = _load_paths()
    scratchllm_path = paths.get("scratchllm_path") or os.environ.get("ALIGN_SCRATCHLLM_PATH")
    if not scratchllm_path or not Path(scratchllm_path).exists():
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Align", "scratchLLM path not set or invalid. Open Settings to set paths?"):
            run_paths_dialog()
        root.destroy()
        scratchllm_path = _load_paths().get("scratchllm_path")
        if not scratchllm_path or not Path(scratchllm_path).exists():
            print("Set scratchllm_path in config/paths.json and run again.", file=sys.stderr)
            sys.exit(1)
    scratchllm_path = Path(scratchllm_path).resolve()
    sys.path.insert(0, str(scratchllm_path))

    data_dir = Path(paths.get("align_data_dir") or os.environ.get("ALIGN_DATA_DIR") or root_path / "data")
    data_dir = data_dir if isinstance(data_dir, Path) else Path(data_dir)
    os.environ["ALIGN_DATA_DIR"] = str(data_dir)
    os.environ["ALIGN_ROOT"] = str(root_path)
    if paths.get("dictionary_path"):
        os.environ["ALIGN_DICTIONARY_PATH"] = str(Path(paths["dictionary_path"]).resolve())

    # Onboarding if no profile
    if not (data_dir / "profile.json").exists() or os.environ.get("ALIGN_ONBOARDING") == "1":
        from Align.onboarding import run_onboarding_ui, bootstrap_mirror_from_profile, sync_mirror_to_scratchllm
        profile = run_onboarding_ui(data_dir, edit_mode=False)
        if profile:
            bootstrap_mirror_from_profile(profile, data_dir)
            sync_mirror_to_scratchllm(scratchllm_path, data_dir)
        from Align.shared_info import refresh_shared_info
        refresh_shared_info(data_dir)

    # Main window
    root = tk.Tk()
    root.title("Align — Retirement & hobby helper")
    root.minsize(500, 520)
    root.geometry("560x600")

    main = ttk.Frame(root, padding=12)
    main.pack(fill=tk.BOTH, expand=True)

    # Agent proactive message
    agent_var = tk.StringVar()
    agent_label = ttk.Label(main, textvariable=agent_var, font=("", 9), foreground="gray", wraplength=520)
    agent_label.pack(anchor=tk.W, pady=(0, 8))
    try:
        from Align.agent import get_proactive_message
        msg = get_proactive_message(data_dir)
        agent_var.set(msg or "")
    except Exception:
        agent_var.set("")

    # Query
    ttk.Label(main, text="Ask about hobbies, retirement, or ask for a helper app:").pack(anchor=tk.W)
    query_var = tk.StringVar()
    query_entry = ttk.Entry(main, textvariable=query_var, width=58)
    query_entry.pack(fill=tk.X, pady=(4, 8))

    def run_query() -> None:
        q = query_var.get().strip()
        if not q:
            return
        try:
            from Align.respond_bridge import query as bridge_query
            tb = _mirror_truth_base_path()
            response, source, _ = bridge_query(q, truth_base_path=tb, use_dictionary=True)
            response_text.delete("1.0", tk.END)
            response_text.insert(tk.END, response)
            if source:
                response_text.insert(tk.END, f"\n\n[Source: {source}]", "source")
        except Exception as e:
            response_text.delete("1.0", tk.END)
            response_text.insert(tk.END, f"Error: {e}")


    response_text = scrolledtext.ScrolledText(main, height=12, wrap=tk.WORD, font=("", 10))
    response_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    response_text.tag_config("source", foreground="gray")

    last_query_var = tk.StringVar()
    last_response_var = tk.StringVar()

    def on_ask() -> None:
        last_query_var.set(query_var.get())
        run_query()
        last_response_var.set(response_text.get("1.0", tk.END))

    ttk.Button(main, text="Ask", command=on_ask).pack(anchor=tk.W, pady=(0, 8))

    def remember_this() -> None:
        q = last_query_var.get().strip()
        r = response_text.get("1.0", tk.END).strip()
        if not q and not r:
            messagebox.showinfo("Remember this", "Ask something first, then click Remember this.")
            return
        if q:
            _append_to_mirror(f"User asked: {q}", "user_note")
        if r and r != "Error: ...":
            _append_to_mirror(f"Assistant said: {r[:400]}", "memory", tier=2)
        messagebox.showinfo("Remember this", "Saved to your Mirror.")

    def record_outcome() -> None:
        win = tk.Toplevel(root)
        win.title("Record outcome")
        win.geometry("400x180")
        ttk.Label(win, text="What did you try?").pack(anchor=tk.W, padx=10, pady=(10, 2))
        desc_var = tk.StringVar()
        ttk.Entry(win, textvariable=desc_var, width=50).pack(fill=tk.X, padx=10, pady=(0, 8))
        ttk.Label(win, text="Result:").pack(anchor=tk.W, padx=10, pady=(0, 2))
        result_var = tk.StringVar(value="success")
        ttk.Combobox(win, textvariable=result_var, values=["success", "failure", "skipped"], state="readonly", width=12).pack(anchor=tk.W, padx=10, pady=(0, 8))
        def submit() -> None:
            d = desc_var.get().strip()
            if d:
                _append_to_mirror(f"Outcome: {d} — {result_var.get()}", "outcome")
                messagebox.showinfo("Record outcome", "Saved.", parent=win)
            win.destroy()
        ttk.Button(win, text="Save", command=submit).pack(pady=10)
        ttk.Button(win, text="Cancel", command=win.destroy).pack()

    actions = ttk.Frame(main)
    actions.pack(fill=tk.X, pady=(0, 8))
    ttk.Button(actions, text="Remember this", command=remember_this).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(actions, text="Record outcome", command=record_outcome).pack(side=tk.LEFT, padx=(0, 8))

    def edit_profile() -> None:
        from Align.onboarding import run_onboarding_ui, bootstrap_mirror_from_profile, sync_mirror_to_scratchllm
        profile = run_onboarding_ui(data_dir, edit_mode=True)
        if profile:
            bootstrap_mirror_from_profile(profile, data_dir)
            sync_mirror_to_scratchllm(scratchllm_path, data_dir)
            from Align.shared_info import refresh_shared_info
            refresh_shared_info(data_dir)
            messagebox.showinfo("Profile", "Profile and Mirror updated.")

    def build_app_cmd() -> None:
        desc = query_var.get().strip() or "a hobby and retirement helper"
        script = root_path / "scripts" / "build_app.py"
        if not script.exists():
            messagebox.showerror("Build app", "scripts/build_app.py not found.")
            return
        env = os.environ.copy()
        env["ALIGN_DATA_DIR"] = str(data_dir)
        try:
            r = subprocess.run([sys.executable, str(script), desc], cwd=str(root_path), env=env, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                messagebox.showinfo("Build app", r.stdout or "App built. Check data/builds/.")
            else:
                messagebox.showerror("Build app", r.stderr or "Build failed.")
        except Exception as e:
            messagebox.showerror("Build app", str(e))

    def one_click_build() -> None:
        from Align.onboarding import load_profile
        p = load_profile(data_dir)
        hobby = (p.get("hobby") or "hobby").strip()
        query_var.set(f"a {hobby} tracker and reminder for my retirement")
        build_app_cmd()

    def train_mirror() -> None:
        train_script = scratchllm_path / "scripts" / "train_model.py"
        corpus_dir = data_dir / "mirror"
        if not (corpus_dir / "truth_base.jsonl").exists():
            messagebox.showinfo("Train Mirror", "Add more to your Mirror first (Ask, Remember this).")
            return
        if not train_script.exists():
            messagebox.showinfo("Train Mirror", "scratchLLM train_model.py not found.")
            return
        env = os.environ.copy()
        env["PYTHONPATH"] = str(scratchllm_path)
        try:
            subprocess.run([sys.executable, str(train_script), str(corpus_dir), "--epochs", "2"], cwd=str(scratchllm_path), env=env, timeout=300)
            messagebox.showinfo("Train Mirror", "Training finished (if no errors).")
        except Exception as e:
            messagebox.showerror("Train Mirror", str(e))

    def on_ask() -> None:
        last_query_var.set(query_var.get())
        run_query()
        last_response_var.set(response_text.get("1.0", tk.END))

    ttk.Button(actions, text="Edit profile", command=edit_profile).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(actions, text="Build app", command=build_app_cmd).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(actions, text="Build my helper app", command=one_click_build).pack(side=tk.LEFT, padx=(0, 8))

    menubar = tk.Menu(root)
    root.config(menu=menubar)
    def sync_traces() -> None:
        try:
            from Align.episodic import sync_traces_to_mirror
            n = sync_traces_to_mirror(data_dir)
            messagebox.showinfo("Sync traces", f"Added {n} exchange(s) to your Mirror." if n else "Nothing new to sync.")
        except Exception as e:
            messagebox.showerror("Sync traces", str(e))

    m_settings = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Settings", menu=m_settings)
    m_settings.add_command(label="Paths...", command=lambda: run_paths_dialog())
    m_settings.add_command(label="Train Mirror model...", command=train_mirror)
    m_settings.add_command(label="Sync traces to Mirror...", command=sync_traces)
    m_health = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Health", menu=m_health)
    m_health.add_command(label="Medications / supplements...", command=lambda: __import__("Align.meds_appointments", fromlist=["run_meds_dialog"]).run_meds_dialog(data_dir))
    m_health.add_command(label="Appointments...", command=lambda: __import__("Align.meds_appointments", fromlist=["run_appointments_dialog"]).run_appointments_dialog(data_dir))

    query_entry.bind("<Return>", lambda e: on_ask())

    def _update_focus_set() -> None:
        try:
            from Align.focus_set import update_focus_set as do_update
            do_update(data_dir)
        except Exception:
            pass
    root.after(3000, _update_focus_set)

    root.mainloop()