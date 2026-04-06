"""
pipeline/shared_state.py
Thread-safe singleton that stores the latest pipeline recognition results
and status. Routes read from this without ever blocking the pipeline.
"""
from __future__ import annotations
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from app.pipeline.config import RESULT_TTL_SEC


# --------------------------------------------------------------------------- #
# Result data class
# --------------------------------------------------------------------------- #
@dataclass
class RecognitionResult:
    person_id:     int
    name:          str
    similarity:    float
    confidence:    float
    bbox:          tuple[int, int, int, int]   # x, y, w, h
    frame_index:   int
    timestamp:     float = field(default_factory=time.time)
    snapshot_path: Optional[str] = None
    source:        str = ""


# --------------------------------------------------------------------------- #
# Shared state
# --------------------------------------------------------------------------- #
class PipelineState:
    """
    Thread-safe container for live pipeline state.
    A single module-level instance is shared across all threads.
    """

    def __init__(self, max_results: int = 200, ttl: int = RESULT_TTL_SEC):
        self._lock          = threading.RLock()
        self._results:  deque[RecognitionResult] = deque(maxlen=max_results)
        self._ttl           = ttl
        self._is_running    = False
        self._source        = ""
        self._frame_count   = 0
        self._fps           = 0.0
        self._last_ts       = 0.0
        self._error: Optional[str] = None

    # ── Mutators ────────────────────────────────────────────────────────────────

    def set_running(self, running: bool, source: str = ""):
        with self._lock:
            self._is_running = running
            if source:
                self._source = source
            if not running:
                self._error = None

    def set_error(self, msg: str):
        with self._lock:
            self._error      = msg
            self._is_running = False

    def tick_frame(self):
        """Call once per processed frame to keep FPS estimate fresh."""
        with self._lock:
            now = time.time()
            if self._last_ts > 0:
                elapsed = now - self._last_ts
                inst    = 1.0 / elapsed if elapsed > 0 else 0.0
                self._fps = 0.1 * inst + 0.9 * self._fps   # EMA
            self._last_ts    = now
            self._frame_count += 1

    def add_result(self, r: RecognitionResult):
        with self._lock:
            self._results.append(r)

    def add_results(self, rs: list[RecognitionResult]):
        with self._lock:
            self._results.extend(rs)

    def clear_results(self):
        with self._lock:
            self._results.clear()

    # ── Accessors ───────────────────────────────────────────────────────────────

    def get_latest_results(self, limit: int = 20, since: float = 0.0) -> list[dict]:
        """Return newest results as JSON-serialisable dicts, honouring TTL."""
        cutoff = time.time() - self._ttl
        with self._lock:
            filtered = [
                r for r in reversed(self._results)
                if r.timestamp > cutoff and r.timestamp > since
            ]
        return [self._to_dict(r) for r in filtered[:limit]]

    def get_status(self) -> dict:
        with self._lock:
            return {
                "is_running":    self._is_running,
                "source":        self._source,
                "frame_count":   self._frame_count,
                "fps":           round(self._fps, 2),
                "total_results": len(self._results),
                "error":         self._error,
            }

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    # ── Serialisation ───────────────────────────────────────────────────────────

    @staticmethod
    def _to_dict(r: RecognitionResult) -> dict:
        return {
            "person_id":     r.person_id,
            "name":          r.name,
            "similarity":    r.similarity,
            "confidence":    r.confidence,
            "bbox":          list(r.bbox),
            "frame_index":   r.frame_index,
            "timestamp":     r.timestamp,
            "snapshot_path": r.snapshot_path,
            "source":        r.source,
        }


# Module-level singleton shared across all threads / routes
pipeline_state = PipelineState()
