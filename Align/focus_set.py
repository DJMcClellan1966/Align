"""
Twin-driven pre-focus: current interests and likely queries from Mirror + profile.
Updates a focus set (terms, optional likely_queries) used by concept_style_retrieval to pre-focus
the dictionary or choose which genre slice to emphasize.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

def _align_data_dir() -> Path:
    import os
    d = os.environ.get("ALIGN_DATA_DIR") or os.environ.get("ALIGN_ROOT")
    if d:
        p = Path(d)
        return p / "data" if "data" not in str(p).replace("\\", "/").split("/")[-1] else p
    return Path(__file__).resolve().parent.parent / "data"


def _extract_terms(text: str, min_len: int = 3, max_terms: int = 30) -> list[str]:
    """Simple word extraction (title case or capitalized words, or key nouns)."""
    if not (text or "").strip():
        return []
    tokens = re.findall(r"[A-Za-z][a-z]+", text)
    stop = frozenset("the and for with are was were have has had this that from your you can will".split())
    out = [t for t in tokens if len(t) >= min_len and t.lower() not in stop]
    return list(dict.fromkeys(out))[:max_terms]


def get_focus_set(data_dir: Optional[Path] = None) -> dict[str, Any]:
    """Read focus set from data/mirror/focus_set.json. Keys: terms, likely_queries."""
    data_dir = data_dir or _align_data_dir()
    path = data_dir / "mirror" / "focus_set.json"
    if not path.exists():
        return {"terms": [], "likely_queries": []}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "terms": data.get("terms") or [],
            "likely_queries": data.get("likely_queries") or [],
        }
    except (json.JSONDecodeError, OSError):
        return {"terms": [], "likely_queries": []}


def update_focus_set(data_dir: Optional[Path] = None) -> dict[str, Any]:
    """
    Build focus set from shared_info concepts + recent Mirror truth_base (extract terms).
    Write to data/mirror/focus_set.json. Call on idle or periodically.
    """
    data_dir = data_dir or _align_data_dir()
    terms: list[str] = []
    likely_queries: list[str] = []
    try:
        from .shared_info import load_shared_info
        shared = load_shared_info(data_dir)
        concepts = shared.get("concepts") or []
        for c in concepts:
            if isinstance(c, str) and c.strip():
                terms.append(c.strip())
            elif isinstance(c, dict) and c.get("name"):
                terms.append(str(c["name"]).strip())
    except Exception:
        pass
    mirror_tb = data_dir / "mirror" / "truth_base.jsonl"
    if mirror_tb.exists():
        try:
            with open(mirror_tb, encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines[-50:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = (obj.get("text") or "").strip()
                    if text:
                        terms.extend(_extract_terms(text, min_len=3, max_terms=15))
                        if "?" in text or "ask" in text.lower() or "what" in text.lower():
                            likely_queries.append(text[:120])
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
    terms = list(dict.fromkeys(terms))[:60]
    likely_queries = list(dict.fromkeys(likely_queries))[:10]
    out = {"terms": terms, "likely_queries": likely_queries}
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "mirror").mkdir(parents=True, exist_ok=True)
    path = data_dir / "mirror" / "focus_set.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    except OSError:
        pass
    return out
