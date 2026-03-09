"""Truth base store: load/save tier 0-2 statements. Standalone for YOUI backend."""
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Statement:
    """Single statement in the truth base."""

    text: str
    tier: int  # 0, 1, or 2
    source: str = "curated"
    category: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = {"text": self.text, "tier": self.tier, "source": self.source}
        if self.category is not None:
            d["category"] = self.category
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Statement":
        return cls(
            text=d.get("text", ""),
            tier=int(d.get("tier", 0)),
            source=d.get("source", "curated"),
            category=d.get("category"),
        )


def load_truth_base(path: str | Path) -> list[Statement]:
    """Load truth base from JSONL."""
    path = Path(path)
    if not path.exists():
        return []
    statements: list[Statement] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            statements.append(Statement.from_dict(json.loads(line)))
    return statements


def save_truth_base(
    statements: list[Statement],
    path: str | Path,
) -> None:
    """Save truth base to JSONL."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for s in statements:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
