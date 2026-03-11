"""
Episodic trace: log each interaction (query, concepts used, answer, source).
Periodically or on demand: sync traces to Mirror (high-value exchanges) or update interest weights.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

def _align_data_dir() -> Path:
    d = os.environ.get("ALIGN_DATA_DIR") or os.environ.get("ALIGN_ROOT")
    if d:
        p = Path(d)
        return p / "data" if "data" not in str(p).replace("\\", "/").split("/")[-1] else p
    return Path(__file__).resolve().parent.parent / "data"


def episodic_path(data_dir: Optional[Path] = None) -> Path:
    data_dir = data_dir or _align_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "episodic.jsonl"


def log_trace(
    query: str,
    response: str,
    source: str,
    concepts_used: Optional[list[str]] = None,
    data_dir: Optional[Path] = None,
) -> None:
    """Append one interaction to episodic.jsonl. Keys: query, response, source, concepts_used, (optional) timestamp."""
    path = episodic_path(data_dir)
    concepts_used = concepts_used or []
    record = {
        "query": (query or "")[:500],
        "response": (response or "")[:2000],
        "source": source or "",
        "concepts_used": concepts_used[:50],
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _load_traces(data_dir: Path, limit: int = 500) -> list[dict]:
    path = episodic_path(data_dir)
    if not path.exists():
        return []
    out: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def sync_traces_to_mirror(
    data_dir: Optional[Path] = None,
    min_response_len: int = 40,
    max_add: int = 10,
) -> int:
    """
    From episodic log, take recent high-value exchanges (non-empty response) and append to Mirror truth base.
    Returns number of statements added.
    """
    data_dir = data_dir or _align_data_dir()
    traces = _load_traces(data_dir, limit=100)
    mirror_dir = data_dir / "mirror"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    tb_path = mirror_dir / "truth_base.jsonl"
    added = 0
    seen: set[str] = set()
    for t in reversed(traces):
        if added >= max_add:
            break
        resp = (t.get("response") or "").strip()
        query = (t.get("query") or "").strip()
        if len(resp) < min_response_len:
            continue
        key = (query[:80], resp[:80])
        if key in seen:
            continue
        seen.add(key)
        line = json.dumps({
            "text": f"User asked: {query[:200]}. Assistant: {resp[:400]}.",
            "tier": 2,
            "source": "episodic_sync",
            "category": "memory",
        }, ensure_ascii=False) + "\n"
        try:
            with open(tb_path, "a", encoding="utf-8") as f:
                f.write(line)
            added += 1
        except OSError:
            break
    if added > 0:
        try:
            from .shared_info import refresh_shared_info
            refresh_shared_info(data_dir)
        except Exception:
            pass
    return added
