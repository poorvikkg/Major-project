"""
pipeline/frame_processor.py
Handles video capture from CCTV/webcam/file.
Applies configurable frame skipping, resizing, and BGR→RGB conversion.
"""
from __future__ import annotations
import cv2
import time
import logging
import threading
import queue
from typing import Generator, Optional, Union

import numpy as np

from app.pipeline.config import TARGET_FPS, FRAME_WIDTH, FRAME_HEIGHT, QUEUE_MAXSIZE

logger = logging.getLogger(__name__)


class FrameProcessor:
    """
    Background thread: captures frames from any OpenCV-compatible source,
    applies skip logic based on TARGET_FPS, resizes, and converts to RGB.
    Frames are placed in a thread-safe queue for downstream workers.
    """

    def __init__(
        self,
        source: Union[str, int] = 0,
        target_fps: int = TARGET_FPS,
        width: int = FRAME_WIDTH,
        height: int = FRAME_HEIGHT,
    ):
        self.source     = source
        self.target_fps = max(1, target_fps)
        self.width      = width
        self.height     = height

        self._cap:          Optional[cv2.VideoCapture] = None
        self._running:      bool                       = False
        self._lock:         threading.Lock             = threading.Lock()
        self._frame_queue:  queue.Queue                = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self._thread:       Optional[threading.Thread] = None
        self._source_fps:   float                      = 30.0
        self._frame_skip:   int                        = 1

    # ── Public API ──────────────────────────────────────────────────────────────

    def start(self):
        """Open capture device and start background reading thread."""
        with self._lock:
            if self._running:
                return

            cam = int(self.source) if str(self.source).isdigit() else self.source
            self._cap = cv2.VideoCapture(cam)
            if not self._cap.isOpened():
                raise RuntimeError(f"Cannot open video source: {self.source}")

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # reduce latency

            self._source_fps  = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
            self._frame_skip  = max(1, int(self._source_fps / self.target_fps))

            logger.info(
                f"[FrameProcessor] source={self.source!r}  src_fps={self._source_fps:.1f}"
                f"  target_fps={self.target_fps}  skip={self._frame_skip}"
            )

            self._running = True
            self._thread  = threading.Thread(
                target=self._capture_loop, daemon=True, name="FrameCaptureThread"
            )
            self._thread.start()

    def stop(self):
        """Stop the capture thread and release resources."""
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("[FrameProcessor] Stopped.")

    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Non-blocking get from the frame queue (returns None on timeout)."""
        try:
            return self._frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def frames(self) -> Generator[np.ndarray, None, None]:
        """Generator wrapper over get_frame()."""
        while self._running:
            f = self.get_frame()
            if f is not None:
                yield f

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._frame_queue.qsize()

    # ── Static helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def preprocess(
        frame: np.ndarray,
        width: int  = FRAME_WIDTH,
        height: int = FRAME_HEIGHT,
    ) -> np.ndarray:
        """Resize BGR frame and convert to RGB uint8."""
        resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
        return cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    @staticmethod
    def extract_from_file(
        video_path: str,
        every_n: int    = 10,
        width: int      = FRAME_WIDTH,
        height: int     = FRAME_HEIGHT,
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """
        Yield (frame_index, rgb_frame) tuples from a video file.
        every_n  — process every Nth frame (configurable skip).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if idx % every_n == 0:
                    yield idx, FrameProcessor.preprocess(frame, width, height)
                idx += 1
        finally:
            cap.release()

    # ── Private ─────────────────────────────────────────────────────────────────

    def _capture_loop(self):
        frame_count = 0
        while self._running:
            if not self._cap or not self._cap.isOpened():
                logger.warning("[FrameProcessor] Capture lost.")
                break

            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            frame_count += 1
            if frame_count % self._frame_skip != 0:
                continue

            processed = self.preprocess(frame, self.width, self.height)

            # Drop oldest frame if queue full (keep pipeline fresh)
            if self._frame_queue.full():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self._frame_queue.put(processed)
