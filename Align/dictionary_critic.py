"""
Dictionary as critic: score generated text against the concept graph.
Post-generation step: extract terms -> look up in graph -> dictionary score.
Use to accept/reject, rank candidates, or trigger "add to Mirror" / "suggest correction".
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

# Stopwords for content-word extraction (minimal set)
_STOP = frozenset(
    "a an the is are was were be been being have has had do does did will would could should "
    "may might must shall can to of in for on with at by from as into through during "
    "and or but if then so that this these those it its i you he she we they".split()
)


def _load_config() -> dict:
    root = Path(__file__).resolve().parent.parent
    p = root / "config" / "concept_bridge.json"
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def extract_content_terms(text: str, min_len: int = 2, max_terms: int = 80) -> list[str]:
    """Extract potential content words (alphanumeric tokens, not stopwords)."""
    if not (text or "").strip():
        return []
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", text)
    out = []
    for t in tokens:
        if len(t) >= min_len and t.lower() not in _STOP:
            out.append(t)
    return list(dict.fromkeys(out))[:max_terms]


def terms_in_graph(terms: list[str], engine: Any) -> set[str]:
    """Which terms appear in the dictionary graph (definitions or context)? Returns set of terms that are graph nodes."""
    if not terms or engine is None:
        return set()
    found: set[str] = set()
    try:
        # Check via get_context_for_description for each term or batch
        ctx_fn = getattr(engine, "get_context_for_description", None)
        if not callable(ctx_fn):
            return found
        for term in terms[:50]:
            try:
                ctx = ctx_fn(term)
                if isinstance(ctx, dict) and (ctx.get("concepts") or ctx.get("key_words") or ctx.get("definition_map")):
                    found.add(term)
            except Exception:
                continue
    except Exception:
        pass
    return found


def dictionary_score(response_text: str, engine: Any) -> tuple[float, int, int]:
    """
    Compute dictionary score: fraction of content words that are graph nodes with definitions.
    Returns (score, num_grounded, num_content).
    """
    terms = extract_content_terms(response_text)
    num_content = len(terms)
    if num_content == 0:
        return (1.0, 0, 0)
    grounded = terms_in_graph(terms, engine)
    num_grounded = len(grounded)
    return (num_grounded / num_content, num_grounded, num_content)


def critic_decision(
    score: float,
    accept_threshold: Optional[float] = None,
    low_warn_threshold: Optional[float] = None,
) -> tuple[str, bool]:
    """
    Decide accept/warn/reject from score.
    Returns (decision, should_show_warning) where decision is "accept" | "warn" | "reject".
    """
    cfg = _load_config()
    accept = accept_threshold if accept_threshold is not None else float(cfg.get("critic_accept_threshold", 0.25))
    low = low_warn_threshold if low_warn_threshold is not None else float(cfg.get("critic_low_warn_threshold", 0.15))
    if score >= accept:
        return ("accept", False)
    if score >= low:
        return ("warn", True)
    return ("reject", True)


def score_and_decide(
    response_text: str,
    engine: Any,
) -> dict[str, Any]:
    """
    Full critic step: score response, decide, return dict for GUI/callers.
    Keys: score, num_grounded, num_content, decision, show_warning, message.
    """
    score, num_grounded, num_content = dictionary_score(response_text, engine)
    decision, show_warning = critic_decision(score)
    message = ""
    if decision == "accept" and num_grounded > 0:
        message = "Answer checked against dictionary."
    elif show_warning:
        message = "Low grounding – consider rephrasing or adding with Remember this."
    return {
        "score": round(score, 3),
        "num_grounded": num_grounded,
        "num_content": num_content,
        "decision": decision,
        "show_warning": show_warning,
        "message": message,
    }
