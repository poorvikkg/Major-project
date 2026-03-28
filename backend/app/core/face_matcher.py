"""
core/face_matcher.py
Compares face embeddings using cosine similarity.
"""
from __future__ import annotations
import numpy as np
from app.config import MATCH_THRESHOLD


class FaceMatcher:
    def __init__(self, threshold: float = MATCH_THRESHOLD):
        self.threshold = threshold

    def cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """
        Cosine similarity mapped to [0, 1].
        1.0 = identical  |  0.5 = orthogonal  |  0.0 = opposite
        """
        a = np.array(v1, dtype=np.float64)
        b = np.array(v2, dtype=np.float64)
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float((np.dot(a, b) / (na * nb) + 1.0) / 2.0)

    def is_match(self, similarity: float) -> bool:
        return similarity >= self.threshold

    def find_best(
        self,
        probe: list[float],
        candidates: list[tuple[int, list[float]]],   # [(id, embedding), ...]
    ) -> tuple[int, float] | None:
        """Return (id, similarity) of best match above threshold, or None."""
        best_id, best_sim = None, 0.0
        for cid, emb in candidates:
            sim = self.cosine_similarity(probe, emb)
            if sim > best_sim:
                best_sim, best_id = sim, cid
        if best_id is not None and self.is_match(best_sim):
            return best_id, best_sim
        return None

    def rank_all(
        self,
        probe: list[float],
        candidates: list[tuple[int, list[float]]],
    ) -> list[tuple[int, float]]:
        """
        Return all candidates sorted by similarity descending.
        Only includes those above threshold.
        """
        results = []
        for cid, emb in candidates:
            sim = self.cosine_similarity(probe, emb)
            if self.is_match(sim):
                results.append((cid, sim))
        results.sort(key=lambda x: x[1], reverse=True)
        return results