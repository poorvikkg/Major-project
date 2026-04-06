"""
services/rtsp_service.py
Non-blocking RTSP stream processor.

Architecture:
  CctvStream            — connects to RTSP/webcam, reads frames in a thread
  AnnotatedFrameBuffer  — runs detection+recognition, stores annotated JPEG bytes
  Module-level registry — one stream per source key, shared across requests
"""
from __future__ import annotations

import cv2
import logging
import threading
import time
import queue
from typing import Optional, Generator

import numpy as np

from app.pipeline.face_detector import RetinaFaceDetector
from app.pipeline.face_embedder import ArcFaceEmbedder
from app.pipeline.faiss_index   import FaissIndex
from app.pipeline.shared_state  import pipeline_state, RecognitionResult
from app.pipeline.config        import (
    TARGET_FPS, FRAME_WIDTH, FRAME_HEIGHT,
    SAVE_SNAPSHOTS, SNAPSHOT_DIR,
)

logger = logging.getLogger(__name__)

# ── Colour palette for bounding boxes ────────────────────────────────────────
_MATCH_COLOUR  = (34, 139, 34)    # green — matched face
_DETECT_COLOUR = (0, 120, 215)    # blue  — face detected, no match
_FONT          = cv2.FONT_HERSHEY_SIMPLEX


class CctvStream:
    """
    Reads frames from an RTSP URL (or webcam index) in a background thread.
    Provides the latest raw BGR frame via get_frame().
    """

    def __init__(self, source: str | int, fps: int = TARGET_FPS):
        self.source     = source
        self.target_fps = max(1, fps)
        self._cap:   Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray]       = None
        self._lock   = threading.Lock()
        self._running = False
        self._error:  Optional[str] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        cam = int(self.source) if str(self.source).isdigit() else self.source
        self._cap = cv2.VideoCapture(cam)

        if not self._cap.isOpened():
            self._error = f"Cannot open stream: {self.source}"
            raise RuntimeError(self._error)

        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        src_fps        = self._cap.get(cv2.CAP_PROP_FPS) or 25.0
        self._skip     = max(1, int(src_fps / self.target_fps))
        self._running  = True
        self._thread   = threading.Thread(
            target=self._read_loop, daemon=True, name=f"CctvRead-{self.source}"
        )
        self._thread.start()
        logger.info(f"[CctvStream] Started  src={self.source!r}  skip={self._skip}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
        logger.info(f"[CctvStream] Stopped  src={self.source!r}")

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def is_running(self) -> bool:
        return self._running

    def _read_loop(self):
        count = 0
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                logger.warning(f"[CctvStream] Stream lost: {self.source}")
                time.sleep(0.5)
                continue
            count += 1
            if count % self._skip != 0:
                continue
            with self._lock:
                self._frame = frame


class AnnotatedStreamProcessor:
    """
    Pulls raw frames from a CctvStream, runs the full AI pipeline, and
    stores the latest annotated JPEG bytes for streaming to the frontend.

    Detection results are also pushed into  pipeline_state  so the
    /results endpoint works without extra effort.
    """

    def __init__(
        self,
        cctv: CctvStream,
        faiss_index: FaissIndex,
        source_label: str = "",
    ):
        self._cctv       = cctv
        self._faiss      = faiss_index
        self._label      = source_label
        self._detector   = RetinaFaceDetector()
        self._embedder   = ArcFaceEmbedder()
        self._jpeg_lock  = threading.Lock()
        self._latest_jpg: Optional[bytes] = None
        self._results:    list[dict]      = []
        self._running     = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._process_loop, daemon=True, name="AnnotatedProcessor"
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def latest_jpeg(self) -> Optional[bytes]:
        with self._jpeg_lock:
            return self._latest_jpg

    def latest_results(self) -> list[dict]:
        return list(self._results)

    # ── Private ───────────────────────────────────────────────────────────────

    def _process_loop(self):
        frame_idx = 0
        while self._running:
            bgr = self._cctv.get_frame()
            if bgr is None:
                time.sleep(0.05)
                continue

            frame_idx += 1
            rgb, annotated_bgr, results = self._process_frame(bgr, frame_idx)
            self._results = results

            # Encode as JPEG for MJPEG stream
            ok, buf = cv2.imencode(".jpg", annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ok:
                with self._jpeg_lock:
                    self._latest_jpg = buf.tobytes()

    def _process_frame(
        self, bgr: np.ndarray, frame_idx: int
    ) -> tuple[np.ndarray, np.ndarray, list[dict]]:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        annotated = bgr.copy()
        results: list[dict] = []

        # Resize for model (keep original for annotation)
        h, w = bgr.shape[:2]
        scale_w = w / FRAME_WIDTH
        scale_h = h / FRAME_HEIGHT

        small_rgb = cv2.resize(rgb, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_LINEAR)

        try:
            detections = self._detector.detect_and_align(small_rgb)
        except Exception as e:
            logger.debug(f"[Processor] detect error: {e}")
            detections = []

        for det in detections:
            xs, ys, ws, hs = det.bbox
            # Scale bbox back to original frame size
            x = int(xs * scale_w)
            y = int(ys * scale_h)
            bw = int(ws * scale_w)
            bh = int(hs * scale_h)

            match: Optional[dict] = None
            if det.aligned_face is not None:
                try:
                    emb = self._embedder.embed(det.aligned_face)
                    if emb is not None:
                        match = self._faiss.get_best_match(emb)
                except Exception as e:
                    logger.debug(f"[Processor] embed/search error: {e}")

            if match:
                colour = _MATCH_COLOUR
                label  = f"{match['name']}  {match['confidence']:.1f}%"
                results.append({
                    "person_id":  match["person_id"],
                    "name":       match["name"],
                    "similarity": match["similarity"],
                    "confidence": match["confidence"],
                    "bbox":       [x, y, bw, bh],
                    "frame":      frame_idx,
                    "timestamp":  time.time(),
                })
                # Push to shared pipeline state
                pipeline_state.add_result(RecognitionResult(
                    person_id=match["person_id"],
                    name=match["name"],
                    similarity=match["similarity"],
                    confidence=match["confidence"],
                    bbox=(x, y, bw, bh),
                    frame_index=frame_idx,
                    source=self._label,
                ))
            else:
                colour = _DETECT_COLOUR
                label  = "Unknown"

            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), colour, 2)
            # Label background
            (tw, th), _ = cv2.getTextSize(label, _FONT, 0.55, 1)
            cv2.rectangle(annotated, (x, y - th - 8), (x + tw + 6, y), colour, -1)
            cv2.putText(annotated, label, (x + 3, y - 5), _FONT, 0.55, (255, 255, 255), 1)

        # Timestamp overlay
        ts = time.strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(annotated, ts, (10, h - 10), _FONT, 0.5, (200, 200, 200), 1)

        return rgb, annotated, results


# ── Module-level stream registry ─────────────────────────────────────────────

class _StreamRegistry:
    """Holds at most one active CCTV stream + processor pair."""

    def __init__(self):
        self._lock      = threading.Lock()
        self._cctv:  Optional[CctvStream]               = None
        self._proc:  Optional[AnnotatedStreamProcessor]  = None
        self._source: str                                = ""

    def start(self, source: str | int, faiss_index: FaissIndex, fps: int = TARGET_FPS) -> str:
        """Start (or restart) stream. Returns empty string on success, error message on failure."""
        with self._lock:
            self._stop_internal()
            try:
                cctv = CctvStream(source, fps)
                cctv.start()
                proc = AnnotatedStreamProcessor(cctv, faiss_index, source_label=str(source))
                proc.start()
                self._cctv   = cctv
                self._proc   = proc
                self._source = str(source)
                pipeline_state.set_running(True, source=str(source))
                return ""
            except Exception as e:
                return str(e)

    def stop(self):
        with self._lock:
            self._stop_internal()
        pipeline_state.set_running(False)

    def _stop_internal(self):
        if self._proc:
            self._proc.stop()
            self._proc = None
        if self._cctv:
            self._cctv.stop()
            self._cctv = None

    def mjpeg_generator(self) -> Generator[bytes, None, None]:
        """Yield MJPEG frames for StreamingResponse."""
        while True:
            jpg = self._proc.latest_jpeg() if self._proc else None
            if jpg is None:
                time.sleep(0.04)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpg
                + b"\r\n"
            )

    def latest_results(self) -> list[dict]:
        if self._proc:
            return self._proc.latest_results()
        return []

    @property
    def is_running(self) -> bool:
        return self._cctv is not None and self._cctv.is_running

    @property
    def source(self) -> str:
        return self._source


# Singleton used by the route module
stream_registry = _StreamRegistry()
