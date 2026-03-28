"""
core/face_detector.py
Detects faces in images using OpenCV Haar cascades or DeepFace.
"""
from __future__ import annotations
import numpy as np
import cv2
from pathlib import Path


class FaceDetector:
    def __init__(self):
        self._cascade = None
        self._deepface = None
        self._mode = "stub"
        self._load()

    def _load(self):
        try:
            from deepface import DeepFace
            self._deepface = DeepFace
            self._mode = "deepface"
        except ImportError:
            pass

        try:
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(path)
            if self._mode != "deepface":
                self._mode = "opencv"
        except Exception:
            pass

    @property
    def mode(self) -> str:
        return self._mode

    def detect_from_path(self, image_path: str | Path) -> list[tuple[int, int, int, int]]:
        img = cv2.imread(str(image_path))
        if img is None:
            return []
        return self.detect_from_frame(img)

    def detect_from_frame(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        if self._mode == "opencv" or self._cascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
            )
            if len(faces) == 0:
                return []
            return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]
        return []

    def draw_boxes(self, frame: np.ndarray,
                   boxes: list[tuple[int, int, int, int]],
                   color: tuple = (0, 255, 100),
                   label: str = "") -> np.ndarray:
        out = frame.copy()
        for (x, y, w, h) in boxes:
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
            if label:
                cv2.putText(out, label, (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        return out

    def count_faces(self, image_path: str | Path) -> int:
        return len(self.detect_from_path(image_path))