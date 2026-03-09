"""User memory / learning: persist queries, feedback, and useful results for personalization."""
import json
from pathlib import Path
from typing import Any
from datetime import datetime

MEMORY_DIR = Path(__file__).resolve().parent.parent / "data" / "memory"


def _ensure_memory_dir(helper_id: str) -> Path:
    d = MEMORY_DIR / helper_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _memory_file(helper_id: str) -> Path:
    return _ensure_memory_dir(helper_id) / "user_layer.jsonl"


def append_feedback(helper_id: str, query: str, response: str, useful: bool, note: str = "") -> None:
    """Record a query, response, and whether it was useful."""
    path = _memory_file(helper_id)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "response": response[:500] if response else "",
        "useful": useful,
        "note": note,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_recent_feedback(helper_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Load recent feedback entries for a helper."""
    path = _memory_file(helper_id)
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.reverse()
    return entries[:limit]


def get_useful_context(helper_id: str, limit: int = 20) -> list[str]:
    """Return recent queries and responses marked useful, for injection into prompts."""
    entries = get_recent_feedback(helper_id, limit=limit * 2)
    useful = [e for e in entries if e.get("useful") is True][:limit]
    return [f"Q: {e.get('query', '')} → {e.get('response', '')}" for e in useful]
