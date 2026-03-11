"""
Concept-grounded style retrieval: concept bundle + genre sentences by concept.
Bridge between dictionary (concept space) and scratchLLM (style/content).
Supports register-aware retrieval (definitional vs narrative) when intent is provided.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

# Concept bundle structure: explicit conditioning for the twin
CONCEPT_BUNDLE_KEYS = ("node_ids", "terms", "definitions")


def _align_data_dir() -> Path:
    d = os.environ.get("ALIGN_DATA_DIR") or os.environ.get("ALIGN_ROOT")
    if d:
        p = Path(d)
        return p / "data" if "data" not in str(p).replace("\\", "/").split("/")[-1] else p
    return Path(__file__).resolve().parent.parent / "data"


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


def get_concept_bundle_from_engine(question: str, engine: Any) -> dict[str, Any]:
    """
    Build concept bundle from dictionary engine (query + graph).
    Returns {"node_ids": [], "terms": [], "definitions": {}}.
    Uses get_context_for_description or process when available.
    """
    bundle: dict[str, Any] = {"node_ids": [], "terms": [], "definitions": {}}
    if engine is None:
        return bundle
    try:
        # Prefer context API if present (concepts, key_words)
        ctx = getattr(engine, "get_context_for_description", None)
        if callable(ctx):
            raw = ctx(question)
            if isinstance(raw, dict):
                for k in ("concepts", "key_words", "key_words_list"):
                    val = raw.get(k)
                    if isinstance(val, list):
                        for c in val:
                            term = c.get("name") if isinstance(c, dict) else c
                            if isinstance(term, str) and term.strip():
                                bundle["terms"].append(term.strip())
                defs = raw.get("definitions") or raw.get("definition_map")
                if isinstance(defs, dict):
                    bundle["definitions"].update(defs)
        # Also try process() for terms in response
        proc = getattr(engine, "process", None)
        if callable(proc):
            result = proc(question)
            if result and getattr(result, "response", None):
                # Simple extract: words that look like concepts (title case or known)
                pass  # terms already from context
    except Exception:
        pass
    bundle["terms"] = list(dict.fromkeys(bundle["terms"]))
    return bundle


def get_concept_bundle_from_shared_info(data_dir: Path) -> dict[str, Any]:
    """Build a minimal concept bundle from shared_info (profile + Mirror concepts) when dictionary is unavailable."""
    bundle: dict[str, Any] = {"node_ids": [], "terms": [], "definitions": {}}
    try:
        from .shared_info import load_shared_info
        shared = load_shared_info(data_dir)
        concepts = shared.get("concepts") or []
        for c in concepts:
            if isinstance(c, str) and c.strip():
                bundle["terms"].append(c.strip())
            elif isinstance(c, dict) and c.get("name"):
                bundle["terms"].append(str(c["name"]).strip())
    except Exception:
        pass
    bundle["terms"] = list(dict.fromkeys(bundle["terms"]))
    return bundle


def _register_tag(sentence: str) -> str:
    """Heuristic: definitional (X is a Y) vs narrative/expository."""
    s = (sentence or "").strip().lower()
    if not s:
        return "narrative"
    # Short and contains " is " / " are " often definitional
    if len(s) < 120 and re.search(r"\b(is|are|means|defined as)\s+", s):
        return "definitional"
    return "narrative"


def load_genre_sentences(data_dir: Path, genre_id: str = "retirement", limit: int = 100) -> list[dict]:
    """Load genre sentences from data/<genre_id>/genre_sentences.jsonl. Each item has text, source, reference, optional register."""
    out: list[dict] = []
    path = data_dir / genre_id / "genre_sentences.jsonl"
    if not path.exists():
        return out
    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and obj.get("text"):
                        if "register" not in obj:
                            obj = dict(obj)
                            obj["register"] = _register_tag(obj["text"])
                        out.append(obj)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def _score_sentence_concept_overlap(sentence: str, terms: list[str]) -> int:
    """Count how many concept terms appear in the sentence (case-insensitive)."""
    if not terms:
        return 0
    s = (sentence or "").lower()
    return sum(1 for t in terms if t and t.lower() in s)


def get_style_sentences(
    concept_bundle: dict[str, Any],
    data_dir: Path,
    genre_id: str = "retirement",
    max_sentences: int = 15,
    register: Optional[str] = None,
) -> list[str]:
    """
    Select genre sentences that overlap with the concept bundle (by term match).
    If register is "definitional" or "narrative", filter to that register; else return mixed.
    """
    terms = concept_bundle.get("terms") or []
    raw = load_genre_sentences(data_dir, genre_id=genre_id, limit=200)
    if not raw:
        return []
    # Score and sort by overlap (then by register if filter)
    scored: list[tuple[int, str, str]] = []
    for obj in raw:
        text = (obj.get("text") or "").strip()
        if not text:
            continue
        reg = obj.get("register", _register_tag(text))
        if register and reg != register:
            continue
        score = _score_sentence_concept_overlap(text, terms)
        scored.append((score, text, reg))
    # Prefer concept overlap; then take top max_sentences
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [text for _, text, _ in scored[:max_sentences]]


def retrieve(
    question: str,
    engine: Any,
    data_dir: Optional[Path] = None,
    genre_id: str = "retirement",
    register: Optional[str] = None,
    max_style: int = 15,
    use_focus_set: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    """
    Concept retrieval + genre style retrieval.
    When use_focus_set is True, merges twin-driven focus set (current interests) into concept bundle terms.
    Returns (concept_bundle, style_sentences) for use in respond_bridge (merge style into retrieval pool, condition on bundle).
    """
    data_dir = data_dir or _align_data_dir()
    concept_bundle = get_concept_bundle_from_engine(question, engine)
    if not concept_bundle.get("terms"):
        concept_bundle = get_concept_bundle_from_shared_info(data_dir)
    if use_focus_set:
        try:
            from .focus_set import get_focus_set
            focus = get_focus_set(data_dir)
            focus_terms = focus.get("terms") or []
            if focus_terms:
                concept_bundle = dict(concept_bundle)
                concept_bundle["terms"] = list(dict.fromkeys((concept_bundle.get("terms") or []) + focus_terms))
        except Exception:
            pass
    style_sentences = get_style_sentences(
        concept_bundle, data_dir, genre_id=genre_id, max_sentences=max_style, register=register
    )
    return (concept_bundle, style_sentences)


def intent_to_register(question: str) -> Optional[str]:
    """
    Simple intent: "what is X" / "define" -> definitional; "tell me a story" / "example" -> narrative.
    Returns "definitional", "narrative", or None for mixed.
    """
    q = (question or "").strip().lower()
    if re.search(r"\b(what is|define|definition of|meaning of)\b", q):
        return "definitional"
    if re.search(r"\b(story|example|for instance|in context)\b", q):
        return "narrative"
    return None
