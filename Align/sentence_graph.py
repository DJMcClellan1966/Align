"""
Sentence-sentence graph: latent structure from shared concepts (word overlap).
Two sentences linked if they share >= k word tokens or high Jaccard similarity.
Use for: "another sentence like this", "expand this idea" (walk neighbors), clustering.
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


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens (alphanumeric), min length 2."""
    if not text:
        return set()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9]{1,}", (text or "").lower())
    return {t for t in tokens if len(t) >= 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def load_sentences_for_graph(data_dir: Path, genre_id: str = "retirement", limit: int = 500) -> list[tuple[str, set[str]]]:
    """Load sentences and their token sets from genre_sentences.jsonl."""
    path = data_dir / genre_id / "genre_sentences.jsonl"
    out: list[tuple[str, set[str]]] = []
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
                    text = (obj.get("text") or "").strip()
                    if text:
                        out.append((text, _tokenize(text)))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def build_graph(
    sentences: list[tuple[str, set[str]]],
    min_shared: int = 2,
    jaccard_min: float = 0.2,
) -> dict[int, list[int]]:
    """
    Build adjacency list: node index -> list of neighbor indices.
    Edge if shared tokens >= min_shared OR Jaccard >= jaccard_min.
    """
    cfg = _load_config()
    k = min_shared if min_shared >= 0 else int(cfg.get("sentence_graph_min_shared_concepts", 2))
    jmin = jaccard_min if jaccard_min >= 0 else float(cfg.get("jaccard_min_similarity", 0.2))
    n = len(sentences)
    adj: dict[int, list[int]] = {i: [] for i in range(n)}
    for i in range(n):
        _, set_i = sentences[i]
        for j in range(i + 1, n):
            _, set_j = sentences[j]
            shared = len(set_i & set_j)
            jacc = _jaccard(set_i, set_j)
            if shared >= k or jacc >= jmin:
                adj[i].append(j)
                adj[j].append(i)
    return adj


def get_similar_sentences(
    sentence: str,
    data_dir: Optional[Path] = None,
    genre_id: str = "retirement",
    top_k: int = 5,
) -> list[str]:
    """Return sentences most similar to the given sentence (same genre pool, by Jaccard on tokens)."""
    data_dir = data_dir or _align_data_dir()
    pool = load_sentences_for_graph(data_dir, genre_id=genre_id)
    if not pool:
        return []
    tok = _tokenize(sentence)
    if not tok:
        return [p[0] for p in pool[:top_k]]
    scored = []
    for text, tset in pool:
        if (text or "").strip() == (sentence or "").strip():
            continue
        j = _jaccard(tok, tset)
        scored.append((j, text))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:top_k]]


def expand_idea(
    sentence: str,
    data_dir: Optional[Path] = None,
    genre_id: str = "retirement",
    depth: int = 1,
    max_sentences: int = 10,
) -> list[str]:
    """Walk the sentence graph from neighbors of the given sentence (expand this idea)."""
    data_dir = data_dir or _align_data_dir()
    pool = load_sentences_for_graph(data_dir, genre_id=genre_id)
    if not pool:
        return []
    adj = build_graph(pool)
    tok = _tokenize(sentence)
    # Find best matching node
    best_idx = -1
    best_j = -1.0
    for i, (_, tset) in enumerate(pool):
        j = _jaccard(tok, tset)
        if j > best_j:
            best_j = j
            best_idx = i
    if best_idx < 0:
        return []
    seen = {best_idx}
    out: list[str] = [pool[best_idx][0]]
    frontier = list(adj.get(best_idx, []))
    for _ in range(depth):
        next_frontier: list[int] = []
        for idx in frontier:
            if idx in seen or len(out) >= max_sentences:
                continue
            seen.add(idx)
            out.append(pool[idx][0])
            next_frontier.extend(adj.get(idx, []))
        frontier = [x for x in next_frontier if x not in seen]
        if not frontier:
            break
    return out[:max_sentences]
