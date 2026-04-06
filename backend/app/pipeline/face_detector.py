"""
pipeline/face_detector.py
RetinaFace-based face detection with 5-point landmark extraction
and proper face alignment (similarity transform → 112×112 crop).

Priority:
  1. insightface  (RetinaFace, buffalo_sc model)
  2. deepface     (retinaface backend)
  3. OpenCV Haar  (offline fallback — no landmarks)
"""
from __future__ import annotations
import cv2
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from app.pipeline.config import MIN_FACE_SIZE, DETECTION_CONFIDENCE

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 5-point reference landmarks for ArcFace 112×112 alignment template
# --------------------------------------------------------------------------- #
ARCFACE_SRC = np.array([
    [38.2946,  51.6963],
    [73.5318,  51.5014],
    [56.0252,  71.7366],
    [41.5493,  92.3655],
    [70.7299,  92.2041],
], dtype=np.float32)


# --------------------------------------------------------------------------- #
# Data class
# --------------------------------------------------------------------------- #
@dataclass
class FaceDetection:
    bbox:         tuple[int, int, int, int]        # x, y, w, h  (original image coords)
    landmarks:    Optional[np.ndarray] = None      # (5, 2) float32 or None
    confidence:   float                = 1.0
    aligned_face: Optional[np.ndarray] = None      # RGB 112×112 crop, set by align step


# --------------------------------------------------------------------------- #
# Alignment helper
# --------------------------------------------------------------------------- #
def _align_face(image_rgb: np.ndarray, landmarks: np.ndarray, size: int = 112) -> np.ndarray:
    """Warp face to canonical pose using similarity transform from 5 landmarks."""
    try:
        from skimage.transform import SimilarityTransform
        tform = SimilarityTransform()
        tform.estimate(landmarks, ARCFACE_SRC)
        M = tform.params[:2]
    except ImportError:
        # Pure-OpenCV fallback: use estimateAffinePartial2D
        M, _ = cv2.estimateAffinePartial2D(landmarks, ARCFACE_SRC, method=cv2.RANSAC)

    return cv2.warpAffine(
        image_rgb, M, (size, size),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )


# --------------------------------------------------------------------------- #
# Detector
# --------------------------------------------------------------------------- #
class RetinaFaceDetector:
    """
    Unified face detector.
    Returns FaceDetection objects (with landmarks when available).
    """

    def __init__(
        self,
        min_face_size: int  = MIN_FACE_SIZE,
        confidence:    float = DETECTION_CONFIDENCE,
    ):
        self.min_face_size        = min_face_size
        self.confidence_threshold = confidence

        self._insight_app = None
        self._deepface    = None
        self._cascade:    Optional[cv2.CascadeClassifier] = None
        self._mode        = "stub"
        self._load()

    # ── Init ────────────────────────────────────────────────────────────────────

    def _load(self):
        # 1. insightface (RetinaFace)
        try:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name="buffalo_sc", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            self._insight_app = app
            self._mode = "insightface"
            logger.info("[FaceDetector] insightface RetinaFace loaded  (mode=insightface)")
            return
        except Exception as e:
            logger.debug(f"[FaceDetector] insightface not available, falling back to next provider: {e}")

        # 2. deepface retinaface
        try:
            from deepface import DeepFace          # noqa: F401
            self._deepface = DeepFace
            self._mode = "deepface"
            logger.info("[FaceDetector] DeepFace retinaface backend loaded  (mode=deepface)")
            return
        except Exception as e:
            logger.warning(f"[FaceDetector] deepface not available: {e}")

        # 3. OpenCV Haar cascade
        try:
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(path)
            self._mode = "opencv"
            logger.warning("[FaceDetector] Falling back to OpenCV Haar cascade  (no landmarks)")
        except Exception as e:
            logger.error(f"[FaceDetector] All backends failed: {e}  (mode=stub)")

    @property
    def mode(self) -> str:
        return self._mode

    # ── Public API ──────────────────────────────────────────────────────────────

    def detect(self, image_rgb: np.ndarray) -> list[FaceDetection]:
        """Detect faces in an RGB image. Returns list sorted by confidence desc."""
        if image_rgb is None or image_rgb.size == 0:
            return []
        if self._mode == "insightface":
            return self._detect_insightface(image_rgb)
        if self._mode == "deepface":
            return self._detect_deepface(image_rgb)
        if self._mode == "opencv":
            return self._detect_opencv(image_rgb)
        return []

    def detect_and_align(self, image_rgb: np.ndarray) -> list[FaceDetection]:
        """
        Detect faces → align each crop to 112×112.
        Handles multiple faces per frame.
        Falls back to simple bbox crop when landmarks are absent.
        """
        detections = self.detect(image_rgb)
        result = []
        for det in detections:
            if det.landmarks is not None:
                try:
                    det.aligned_face = _align_face(image_rgb, det.landmarks)
                except Exception as e:
                    logger.debug(f"Alignment failed ({e}) — using bbox crop")
                    det.aligned_face = self._bbox_crop(image_rgb, det.bbox)
            else:
                det.aligned_face = self._bbox_crop(image_rgb, det.bbox)

            if det.aligned_face is not None and det.aligned_face.size > 0:
                result.append(det)
        return result

    # ── Backends ────────────────────────────────────────────────────────────────

    def _detect_insightface(self, image_rgb: np.ndarray) -> list[FaceDetection]:
        try:
            bgr   = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            faces = self._insight_app.get(bgr)
            out   = []
            for f in faces:
                score = float(f.det_score)
                if score < self.confidence_threshold:
                    continue
                x1, y1, x2, y2 = f.bbox.astype(int)
                w, h = x2 - x1, y2 - y1
                if w < self.min_face_size or h < self.min_face_size:
                    continue
                lm = f.kps.astype(np.float32) if f.kps is not None else None
                out.append(FaceDetection(bbox=(x1, y1, w, h), landmarks=lm, confidence=score))
            return sorted(out, key=lambda d: d.confidence, reverse=True)
        except Exception as e:
            logger.error(f"[insightface detect] {e}")
            return []

    def _detect_deepface(self, image_rgb: np.ndarray) -> list[FaceDetection]:
        try:
            bgr    = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            result = self._deepface.extract_faces(
                img_path=bgr,
                detector_backend="retinaface",
                enforce_detection=False,
                align=False,
            )
            out = []
            for fd in result:
                reg  = fd.get("facial_area", {})
                x, y = reg.get("x", 0), reg.get("y", 0)
                w, h = reg.get("w", 0), reg.get("h", 0)
                conf = fd.get("confidence", 1.0)
                if w < self.min_face_size or h < self.min_face_size:
                    continue
                if conf < self.confidence_threshold:
                    continue
                # deepface retinaface returns landmarks under "facial_area" -> "left_eye", etc.
                lm = self._extract_deepface_landmarks(fd)
                out.append(FaceDetection(bbox=(x, y, w, h), landmarks=lm, confidence=conf))
            return sorted(out, key=lambda d: d.confidence, reverse=True)
        except Exception as e:
            logger.error(f"[deepface detect] {e}")
            return []

    @staticmethod
    def _extract_deepface_landmarks(face_data: dict) -> Optional[np.ndarray]:
        """Try to extract 5-point landmarks from DeepFace result."""
        try:
            fa = face_data.get("facial_area", {})
            keys = ["left_eye", "right_eye", "nose", "mouth_left", "mouth_right"]
            pts  = []
            for k in keys:
                val = fa.get(k)
                if val is None:
                    return None
                pts.append([float(val[0]), float(val[1])])
            return np.array(pts, dtype=np.float32)
        except Exception:
            return None

    def _detect_opencv(self, image_rgb: np.ndarray) -> list[FaceDetection]:
        try:
            gray  = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            faces = self._cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5,
                minSize=(self.min_face_size, self.min_face_size),
            )
            if len(faces) == 0:
                return []
            return [
                FaceDetection(bbox=(int(x), int(y), int(w), int(h)), confidence=1.0)
                for x, y, w, h in faces
            ]
        except Exception as e:
            logger.error(f"[opencv detect] {e}")
            return []

    @staticmethod
    def _bbox_crop(image: np.ndarray, bbox: tuple[int, int, int, int]) -> Optional[np.ndarray]:
        x, y, w, h = bbox
        H, W = image.shape[:2]
        x, y   = max(0, x), max(0, y)
        x2, y2 = min(W, x + w), min(H, y + h)
        if x2 <= x or y2 <= y:
            return None
        crop = image[y:y2, x:x2]
        return cv2.resize(crop, (112, 112), interpolation=cv2.INTER_LINEAR)
