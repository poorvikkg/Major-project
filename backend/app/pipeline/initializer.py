"""
pipeline/initializer.py
Load all 'missing' person embeddings from PostgreSQL and populate the FAISS index.
Called once at app startup and whenever the index needs refreshing.
"""
from __future__ import annotations
import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional

from app.pipeline.faiss_index  import FaissIndex
from app.pipeline.shared_state import pipeline_state

logger = logging.getLogger(__name__)


def load_embeddings_into_faiss(db_session, faiss_index: FaissIndex) -> int:
    """
    Query the DB for all missing persons with saved embeddings,
    rebuild the FAISS index, and return the count loaded.
    """
    from app.models.missing_person import MissingPerson

    persons = (
        db_session.query(MissingPerson)
        .filter(MissingPerson.status == "missing")
        .filter(MissingPerson.embedding_path.isnot(None))
        .all()
    )

    candidates: list[tuple[int, str, np.ndarray]] = []
    for p in persons:
        emb = _load_embedding(p.embedding_path)
        if emb is not None:
            candidates.append((p.id, p.name or "", emb))

    faiss_index.rebuild_from_db(candidates)
    logger.info(f"[Initializer] FAISS index loaded with {len(candidates)} embeddings")
    return len(candidates)


def _load_embedding(path: str) -> Optional[np.ndarray]:
    """Read an embedding JSON file and return a float32 numpy array."""
    try:
        p = Path(path)
        if not p.exists():
            logger.warning(f"[Initializer] Embedding file not found: {path}")
            return None
        with open(p) as f:
            data = json.load(f)
        arr = np.array(data, dtype=np.float32)
        if arr.ndim != 1 or arr.size == 0:
            return None
        return arr
    except Exception as e:
        logger.warning(f"[Initializer] Could not load embedding {path}: {e}")
        return None
