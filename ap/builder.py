from __future__ import annotations

import random
from typing import Dict, List


class WordSearchGameBuilder:
    """Builder (creation pattern from prior activity)."""

    def build(self, size: int = 10, words: List[str] | None = None) -> Dict:
        words = words or ["APSI", "INVENIRA", "FACADE", "ADAPTER", "PROXY"]
        random.seed(42)
        return {"size": size, "words": words, "seed": 42}
