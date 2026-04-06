"""
pipeline/faiss_index.py
FAISS-backed vector store for fast cosine similarity face search.

All embeddings are L2-normalised before insertion so that
inner product == cosine similarity.

Index types:
  Flat   — exact, best for < 100k embeddings (default)
  IVF    — approximate, better for 100k+ embeddings
"""
from __future__ import annotations
import json
import logging
import threading
import numpy as np
from pathlib import Path
from typing import Optional

from app.pipeline.config import (
    FAISS_INDEX_TYPE, FAISS_INDEX_PATH, FAISS_META_PATH,
    FAISS_IVF_NLIST, EMBEDDING_DIM, TOP_K, MATCH_THRESHOLD,
)

logger = logging.getLogger(__name__)


class FaissIndex:
    """
    Thread-safe FAISS index wrapper.
    Maps vector positions → {person_id, name, …} via a parallel metadata list.
    Falls back to brute-force numpy search when faiss is not installed.
    """

    def __init__(
        self,
        dim:        int   = EMBEDDING_DIM,
        index_type: str   = FAISS_INDEX_TYPE,
        index_path: Path  = FAISS_INDEX_PATH,
        meta_path:  Path  = FAISS_META_PATH,
        threshold:  float = MATCH_THRESHOLD,
        top_k:      int   = TOP_K,
    ):
        self.dim        = dim
        self.index_type = index_type
        self.index_path = Path(index_path)
        self.meta_path  = Path(meta_path)
        self.threshold  = threshold
        self.top_k      = top_k

        self._lock:    threading.RLock = threading.RLock()
        self._index                    = None
        self._meta:    list[dict]      = []      # [{person_id, name, …}, …]
        self._np_embs: list[np.ndarray] = []     # fallback store
        self._faiss:   object          = None
        self._available: bool          = False

        self._init_faiss()

    # ── Init ────────────────────────────────────────────────────────────────────

    def _init_faiss(self):
        try:
            import faiss
            self._faiss     = faiss
            self._available = True
            self._build_index()
            logger.info(f"[FaissIndex] Ready  type={self.index_type}  dim={self.dim}")
        except ImportError:
            logger.warning("[FaissIndex] faiss not installed — using numpy fallback search")

    def _build_index(self, n: int = 0):
        f = self._faiss
        if self.index_type == "IVF" and n > self.dim:
            nlist = min(FAISS_IVF_NLIST, n)
            q     = f.IndexFlatIP(self.dim)
            self._index = f.IndexIVFFlat(q, self.dim, nlist, f.METRIC_INNER_PRODUCT)
        else:
            self._index = f.IndexFlatIP(self.dim)

    # ── Write API ───────────────────────────────────────────────────────────────

    def add(self, embedding: np.ndarray, person_id: int, name: str = "", **extra):
        """Add a single embedding."""
        vec = self._norm(embedding).reshape(1, -1).astype(np.float32)
        with self._lock:
            if self._available:
                if hasattr(self._index, "is_trained") and not self._index.is_trained:
                    self._index.train(vec)
                self._index.add(vec)
            else:
                self._np_embs.append(vec.reshape(-1))
            self._meta.append({"person_id": person_id, "name": name, **extra})

    def rebuild_from_db(self, candidates: list[tuple[int, str, np.ndarray]]):
        """
        Replace entire index content.
        candidates : [(person_id, name, embedding_array), …]
        """
        with self._lock:
            if self._available:
                self._build_index(len(candidates))
            else:
                self._np_embs = []
            self._meta = []

        if not candidates:
            logger.warning("[FaissIndex] rebuild_from_db called with 0 candidates")
            return

        arr       = np.array([c[2] for c in candidates], dtype=np.float32)
        normed    = np.array([self._norm(e) for e in arr], dtype=np.float32)
        person_ids = [c[0] for c in candidates]
        names      = [c[1] for c in candidates]

        with self._lock:
            if self._available:
                idx = self._index
                if hasattr(idx, "is_trained") and not idx.is_trained:
                    if len(normed) >= getattr(idx, "nlist", 1):
                        idx.train(normed)
                idx.add(normed)
            else:
                self._np_embs = list(normed)
            self._meta = [{"person_id": p, "name": n} for p, n in zip(person_ids, names)]

        logger.info(f"[FaissIndex] Rebuilt with {len(candidates)} embeddings")

    # ── Search API ──────────────────────────────────────────────────────────────

    def search(self, query: np.ndarray, top_k: Optional[int] = None) -> list[dict]:
        """
        Find closest matches for a query embedding.
        Returns list of dicts sorted by similarity (highest first).
        Only values above self.threshold are included.
        """
        k = top_k or self.top_k
        q = self._norm(query).reshape(1, -1).astype(np.float32)

        with self._lock:
            total = len(self._meta)
            if total == 0:
                return []
            k = min(k, total)
            if self._available:
                D, I = self._index.search(q, k)
                raw  = list(zip(I[0], D[0]))
            else:
                raw  = self._numpy_search(q.reshape(-1), k)

        results = []
        for idx, score in raw:
            if idx < 0 or idx >= len(self._meta):
                continue
            # inner product of normed vectors = cosine similarity ∈ [-1, 1]
            cos   = float(np.clip(score, -1.0, 1.0))
            sim01 = (cos + 1.0) / 2.0          # map to [0, 1]
            if sim01 < self.threshold:
                continue
            m = self._meta[idx]
            results.append({
                "person_id":  m["person_id"],
                "name":       m.get("name", ""),
                "similarity": round(sim01, 4),
                "confidence": round(sim01 * 100, 2),
                "match":      True,
                "index":      int(idx),
            })
        return sorted(results, key=lambda r: r["similarity"], reverse=True)

    def get_best_match(self, query: np.ndarray) -> Optional[dict]:
        """Return the single best match above threshold, or None."""
        res = self.search(query, top_k=1)
        return res[0] if res else None

    # ── Persistence ─────────────────────────────────────────────────────────────

    def save(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self._available and self._index is not None:
                self._faiss.write_index(self._index, str(self.index_path))
            with open(self.meta_path, "w") as f:
                json.dump(self._meta, f)
        logger.info(f"[FaissIndex] Saved to {self.index_path}")

    def load(self) -> bool:
        if not self.index_path.exists() or not self.meta_path.exists():
            return False
        try:
            with self._lock:
                if self._available:
                    self._index = self._faiss.read_index(str(self.index_path))
                with open(self.meta_path) as f:
                    self._meta = json.load(f)
            logger.info(f"[FaissIndex] Loaded {len(self._meta)} entries from disk")
            return True
        except Exception as e:
            logger.error(f"[FaissIndex] load failed: {e}")
            return False

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._meta)

    # ── Helpers ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _norm(v: np.ndarray) -> np.ndarray:
        v    = v.astype(np.float32)
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def _numpy_search(self, query: np.ndarray, k: int) -> list[tuple[int, float]]:
        if not self._np_embs:
            return []
        mat    = np.array(self._np_embs, dtype=np.float32)
        scores = mat @ query
        top    = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in top]
