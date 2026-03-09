"""Retrieve relevant statements from truth base for a query (simple keyword match)."""
from pathlib import Path
from typing import Any

from .truth_base import load_truth_base, Statement
from .memory import get_useful_context


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def retrieve(
    query: str,
    truth_base_path: str | Path,
    helper_id: str = "",
    top_k: int = 5,
    include_user_context: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Return (list of statement dicts, list of user-context strings).
    Uses simple keyword overlap for ranking; no embeddings required.
    """
    statements = load_truth_base(truth_base_path)
    if not statements:
        return [], []

    q_norm = _normalize(query)
    q_words = set(q_norm.split())

    scored: list[tuple[float, Statement]] = []
    for s in statements:
        t_norm = _normalize(s.text)
        t_words = set(t_norm.split())
        overlap = len(q_words & t_words) + (0.1 if any(w in t_norm for w in q_words) else 0)
        if overlap > 0 or not q_words:
            scored.append((overlap, s))

    scored.sort(key=lambda x: -x[0])
    results = [s.to_dict() for _, s in scored[:top_k]]

    user_context: list[str] = []
    if include_user_context and helper_id:
        user_context = get_useful_context(helper_id, limit=5)

    return results, user_context
