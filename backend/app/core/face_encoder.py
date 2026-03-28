"""
core/face_encoder.py
Generates FaceNet 128-d / 512-d embedding vectors from face images.

Priority chain:
  1. DeepFace  →  model_name = "Facenet"
  2. DeepFace  →  model_name = "Facenet512"
  3. OpenCV HOG descriptor (offline fallback)
  4. Stub random vector    (demo / CI mode)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from app.config import FACENET_MODEL, DETECTOR_BACKEND


class FaceEncoder:
    def __init__(self):
        self._deepface = None
        self._cascade  = None
        self._mode     = "stub"
        self._load()

    def _load(self):
        try:
            from deepface import DeepFace
            self._deepface = DeepFace
            self._mode = "deepface_facenet"
            print(f"✅  FaceEncoder: DeepFace/{FACENET_MODEL} loaded")
            return
        except ImportError:
            print("⚠️   DeepFace unavailable → OpenCV HOG fallback")

        try:
            import cv2
            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(path)
            self._mode = "opencv_hog"
            print("✅  FaceEncoder: OpenCV HOG mode")
        except Exception as e:
            print(f"⚠️   OpenCV unavailable ({e}) → stub mode")
            self._mode = "stub"

    @property
    def mode(self) -> str:
        return self._mode

    # ── Public API ────────────────────────────────────────────────────────────

    def encode(self, image_path: str | Path) -> list[float] | None:
        """
        Return normalised embedding list or None if no face found.
        """
        path = str(image_path)
        if self._mode == "deepface_facenet":
            return self._encode_deepface(path)
        if self._mode == "opencv_hog":
            return self._encode_opencv(path)
        # stub mode
        return list(np.random.rand(128).tolist())

    def encode_frame(self, frame) -> list[float] | None:
        """Encode directly from a numpy BGR frame."""
        import cv2, tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        cv2.imwrite(tmp.name, frame)
        result = self.encode(tmp.name)
        os.unlink(tmp.name)
        return result

    def save_embedding(self, embedding: list[float], path: str | Path):
        with open(path, "w") as f:
            json.dump(embedding, f)

    def load_embedding(self, path: str | Path) -> list[float] | None:
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    # ── DeepFace backend ──────────────────────────────────────────────────────

    def _encode_deepface(self, path: str) -> list[float] | None:
        models = [FACENET_MODEL, "Facenet512", "Facenet"]
        for model in models:
            for enforce in (True, False):
                try:
                    result = self._deepface.represent(
                        img_path=path,
                        model_name=model,
                        detector_backend=DETECTOR_BACKEND,
                        enforce_detection=enforce,
                        align=True,
                    )
                    if result:
                        emb = np.array(result[0]["embedding"], dtype=np.float64)
                        norm = np.linalg.norm(emb)
                        if norm > 0:
                            emb = emb / norm
                        return emb.tolist()
                except Exception:
                    continue
        return None

    # ── OpenCV HOG fallback ───────────────────────────────────────────────────

    def _encode_opencv(self, path: str) -> list[float] | None:
        try:
            import cv2
            img = cv2.imread(path)
            if img is None:
                return None
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self._cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
            )
            if len(faces) == 0:
                return None
            x, y, w, h = faces[0]
            roi = cv2.resize(gray[y:y+h, x:x+w], (64, 64)).astype(np.float64) / 255.0
            gx = cv2.Sobel(roi, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(roi, cv2.CV_64F, 0, 1, ksize=3)
            mag = np.sqrt(gx**2 + gy**2).flatten()
            step = max(len(mag) // 128, 1)
            desc = mag[::step][:128]
            norm = np.linalg.norm(desc)
            return (desc / norm if norm > 0 else desc).tolist()
        except Exception as e:
            print(f"OpenCV encode error: {e}")
            return None