"""
pipeline/pipeline_manager.py
Non-blocking real-time face recognition pipeline.

Architecture
────────────
  ┌─────────────────────┐   frame queue   ┌──────────────────────────┐
  │  FrameProcessor     │ ──────────────► │  Worker Thread(s)        │
  │  (capture thread)   │                 │  detect → align → embed  │
  └─────────────────────┘                 │  → FAISS search          │
                                          │  → SharedState.add()     │
                                          └──────────────────────────┘
FastAPI routes read from SharedState (never block the pipeline).
"""
from __future__ import annotations
import cv2
import uuid
import logging
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Union

import numpy as np

from app.pipeline.config import (
    TARGET_FPS, FRAME_WIDTH, FRAME_HEIGHT,
    WORKER_THREADS, QUEUE_MAXSIZE,
    SAVE_SNAPSHOTS, SNAPSHOT_DIR,
)
from app.pipeline.frame_processor import FrameProcessor
from app.pipeline.face_detector   import RetinaFaceDetector
from app.pipeline.face_embedder   import ArcFaceEmbedder
from app.pipeline.faiss_index     import FaissIndex
from app.pipeline.shared_state    import pipeline_state, RecognitionResult

logger = logging.getLogger(__name__)


class PipelineManager:
    """
    Orchestrates the full real-time pipeline.
    Call start() → non-blocking.  Call stop() to clean up.
    """

    def __init__(
        self,
        faiss_index: FaissIndex,
        source:      Union[str, int] = 0,
        target_fps:  int             = TARGET_FPS,
        num_workers: int             = WORKER_THREADS,
    ):
        self.faiss_index = faiss_index
        self.source      = source
        self.target_fps  = target_fps
        self.num_workers = num_workers

        self._frame_proc  = FrameProcessor(
            source=source, target_fps=target_fps,
            width=FRAME_WIDTH, height=FRAME_HEIGHT,
        )
        self._work_q:    queue.Queue             = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self._detector:  Optional[RetinaFaceDetector] = None
        self._embedder:  Optional[ArcFaceEmbedder]    = None
        self._workers:   list[threading.Thread]  = []
        self._feeder:    Optional[threading.Thread]   = None
        self._running    = False
        self._lock       = threading.Lock()

        Path(SNAPSHOT_DIR).mkdir(parents=True, exist_ok=True)

    # ── Lifecycle ───────────────────────────────────────────────────────────────

    def start(self):
        """Start capture + worker threads (non-blocking)."""
        with self._lock:
            if self._running:
                logger.warning("[Pipeline] Already running")
                return

            logger.info("[Pipeline] Initialising models …")
            self._lazy_init()
            self._frame_proc.start()
            self._running = True

            self._feeder = threading.Thread(
                target=self._feeder_loop, daemon=True, name="PipelineFeeder"
            )
            self._feeder.start()

            for i in range(self.num_workers):
                t = threading.Thread(
                    target=self._worker_loop, daemon=True, name=f"PipelineWorker-{i}"
                )
                t.start()
                self._workers.append(t)

            pipeline_state.set_running(True, source=str(self.source))
            logger.info(
                f"[Pipeline] Started  source={self.source!r}  fps={self.target_fps}"
                f"  workers={self.num_workers}"
                f"  detector={self._detector.mode}  embedder={self._embedder.mode}"
            )

    def stop(self):
        """Gracefully stop all threads."""
        with self._lock:
            if not self._running:
                return
            self._running = False

        self._frame_proc.stop()

        # Poison pills for workers
        for _ in self._workers:
            try:
                self._work_q.put_nowait(None)
            except queue.Full:
                pass
        for t in self._workers:
            t.join(timeout=3)
        self._workers.clear()

        pipeline_state.set_running(False)
        logger.info("[Pipeline] Stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    def reload_index(self, candidates: list[tuple[int, str, np.ndarray]]):
        """Hot-reload FAISS index without stopping pipeline."""
        self.faiss_index.rebuild_from_db(candidates)
        logger.info(f"[Pipeline] FAISS reloaded  n={len(candidates)}")

    # ── Private ─────────────────────────────────────────────────────────────────

    def _lazy_init(self):
        if self._detector is None:
            self._detector = RetinaFaceDetector()
        if self._embedder is None:
            self._embedder = ArcFaceEmbedder()

    def _feeder_loop(self):
        """Move frames from FrameProcessor queue to the work queue."""
        frame_idx = 0
        while self._running:
            frame = self._frame_proc.get_frame(timeout=1.0)
            if frame is None:
                continue
            frame_idx += 1
            pipeline_state.tick_frame()
            try:
                self._work_q.put_nowait((frame_idx, frame))
            except queue.Full:
                pass   # drop stale frame

    def _worker_loop(self):
        """Consume frames: detect → embed → search → record."""
        while self._running:
            try:
                item = self._work_q.get(timeout=1.0)
            except queue.Empty:
                continue
            if item is None:       # shutdown signal
                break
            frame_idx, frame_rgb = item
            try:
                self._process_frame(frame_idx, frame_rgb)
            except Exception as e:
                logger.error(f"[Worker] frame {frame_idx}: {e}", exc_info=True)
            finally:
                self._work_q.task_done()

    def _process_frame(self, frame_idx: int, frame_rgb: np.ndarray):
        # ① Detect + align
        detections = self._detector.detect_and_align(frame_rgb)
        if not detections:
            return

        results: list[RecognitionResult] = []
        for det in detections:
            if det.aligned_face is None:
                continue

            # ② Embed
            emb = self._embedder.embed(det.aligned_face)
            if emb is None:
                continue

            # ③ FAISS search
            match = self.faiss_index.get_best_match(emb)
            if match is None:
                continue

            # ④ Optionally save annotated snapshot
            snap = self._save_snapshot(frame_rgb, det.bbox, match) if SAVE_SNAPSHOTS else None

            results.append(RecognitionResult(
                person_id=match["person_id"],
                name=match["name"],
                similarity=match["similarity"],
                confidence=match["confidence"],
                bbox=det.bbox,
                frame_index=frame_idx,
                snapshot_path=snap,
                source=str(self.source),
            ))

        if results:
            pipeline_state.add_results(results)
            logger.debug(
                f"[Worker] frame {frame_idx}: {len(results)} match(es) "
                f"— ids={[r.person_id for r in results]}"
            )

    @staticmethod
    def _save_snapshot(
        frame_rgb: np.ndarray,
        bbox:      tuple[int, int, int, int],
        match:     dict,
    ) -> Optional[str]:
        try:
            bgr  = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            x, y, w, h = bbox
            label = f"{match['name']} ({match['confidence']:.1f}%)"
            cv2.rectangle(bgr, (x, y), (x + w, y + h), (0, 255, 100), 2)
            cv2.putText(bgr, label, (x, max(0, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 100), 2)
            fname = f"pl_{match['person_id']}_{uuid.uuid4().hex[:8]}.jpg"
            path  = str(Path(SNAPSHOT_DIR) / fname)
            cv2.imwrite(path, bgr)
            return path
        except Exception as e:
            logger.debug(f"[Snapshot] {e}")
            return None
