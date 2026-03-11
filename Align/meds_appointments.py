"""
Structured meds and appointments: add/edit and persist to Mirror + shared_info.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .onboarding import _align_data_dir
from .shared_info import save_meds, save_appointments, _load_meds, _load_appointments


def run_meds_dialog(data_dir: Optional[Path] = None) -> None:
    """Add or edit medications (name, dose, time). Saves to mirror/meds.json and refreshes shared_info."""
    import tkinter as tk
    from tkinter import ttk, messagebox

    data_dir = data_dir or _align_data_dir()
    meds = _load_meds(data_dir)

    root = tk.Toplevel()
    root.title("Medications & supplements")
    root.geometry("420x320")

    main = ttk.Frame(root, padding=12)
    main.pack(fill=tk.BOTH, expand=True)
    ttk.Label(main, text="Add medication or supplement (name, dose, time):", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 8))

    list_frame = ttk.Frame(main)
    list_frame.pack(fill=tk.BOTH, expand=True)
    lb = tk.Listbox(list_frame, height=6, font=("", 10))
    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    for m in meds:
        lb.insert(tk.END, f"{m.get('name', '')} — {m.get('dose', '')} at {m.get('time', '')}")
    scroll = ttk.Scrollbar(list_frame, command=lb.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    lb.config(yscrollcommand=scroll.set)

    f = ttk.Frame(main)
    f.pack(fill=tk.X, pady=(8, 4))
    ttk.Label(f, text="Name:").pack(side=tk.LEFT, padx=(0, 4))
    name_var = tk.StringVar()
    ttk.Entry(f, textvariable=name_var, width=16).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(f, text="Dose:").pack(side=tk.LEFT, padx=(0, 4))
    dose_var = tk.StringVar()
    ttk.Entry(f, textvariable=dose_var, width=10).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(f, text="Time:").pack(side=tk.LEFT, padx=(0, 4))
    time_var = tk.StringVar()
    ttk.Entry(f, textvariable=time_var, width=10).pack(side=tk.LEFT)

    def add_med() -> None:
        name = name_var.get().strip()
        if not name:
            messagebox.showinfo("Add", "Enter at least a name.", parent=root)
            return
        meds.append({"name": name, "dose": dose_var.get().strip(), "time": time_var.get().strip()})
        save_meds(meds, data_dir)
        lb.insert(tk.END, f"{name} — {dose_var.get()} at {time_var.get()}")
        name_var.set(""); dose_var.set(""); time_var.set("")

    def remove_med() -> None:
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        lb.delete(idx)
        meds.pop(idx)
        save_meds(meds, data_dir)

    btn_f = ttk.Frame(main)
    btn_f.pack(fill=tk.X, pady=8)
    ttk.Button(btn_f, text="Add", command=add_med).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_f, text="Remove selected", command=remove_med).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_f, text="Close", command=root.destroy).pack(side=tk.LEFT)


def run_appointments_dialog(data_dir: Optional[Path] = None) -> None:
    """Add or edit appointments (what, when, where). Saves to mirror/appointments.json and refreshes shared_info."""
    import tkinter as tk
    from tkinter import ttk, messagebox

    data_dir = data_dir or _align_data_dir()
    appointments = _load_appointments(data_dir)

    root = tk.Toplevel()
    root.title("Appointments")
    root.geometry("460x320")

    main = ttk.Frame(root, padding=12)
    main.pack(fill=tk.BOTH, expand=True)
    ttk.Label(main, text="Add appointment (what, when, where):", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 8))

    list_frame = ttk.Frame(main)
    list_frame.pack(fill=tk.BOTH, expand=True)
    lb = tk.Listbox(list_frame, height=6, font=("", 10))
    lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    for a in appointments:
        lb.insert(tk.END, f"{a.get('what', '')} — {a.get('when', '')} @ {a.get('where', '')}")
    scroll = ttk.Scrollbar(list_frame, command=lb.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    lb.config(yscrollcommand=scroll.set)

    f = ttk.Frame(main)
    f.pack(fill=tk.X, pady=(8, 4))
    ttk.Label(f, text="What:").pack(side=tk.LEFT, padx=(0, 4))
    what_var = tk.StringVar()
    ttk.Entry(f, textvariable=what_var, width=18).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(f, text="When:").pack(side=tk.LEFT, padx=(0, 4))
    when_var = tk.StringVar()
    ttk.Entry(f, textvariable=when_var, width=14).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(f, text="Where:").pack(side=tk.LEFT, padx=(0, 4))
    where_var = tk.StringVar()
    ttk.Entry(f, textvariable=where_var, width=14).pack(side=tk.LEFT)

    def add_apt() -> None:
        what = what_var.get().strip()
        if not what:
            messagebox.showinfo("Add", "Enter what the appointment is.", parent=root)
            return
        appointments.append({"what": what, "when": when_var.get().strip(), "where": where_var.get().strip()})
        save_appointments(appointments, data_dir)
        lb.insert(tk.END, f"{what} — {when_var.get()} @ {where_var.get()}")
        what_var.set(""); when_var.set(""); where_var.set("")

    def remove_apt() -> None:
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        lb.delete(idx)
        appointments.pop(idx)
        save_appointments(appointments, data_dir)

    btn_f = ttk.Frame(main)
    btn_f.pack(fill=tk.X, pady=8)
    ttk.Button(btn_f, text="Add", command=add_apt).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_f, text="Remove selected", command=remove_apt).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_f, text="Close", command=root.destroy).pack(side=tk.LEFT)
