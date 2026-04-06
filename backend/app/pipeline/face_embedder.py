"""
pipeline/face_embedder.py
Generates 512-d ArcFace embeddings from aligned face crops (RGB 112×112).

Priority:
  1. insightface ArcFace  (buffalo_sc — 512-d)
  2. deepface  ArcFace    (512-d)
  3. deepface  Facenet512 (512-d fallback)
  4. stub random vector   (CI / offline demo)
"""
from __future__ import annotations
import logging
import numpy as np
from typing import Optional

from app.pipeline.config import EMBEDDING_DIM

logger = logging.getLogger(__name__)


class ArcFaceEmbedder:
    """Generates L2-normalised ArcFace embeddings."""

    def __init__(self):
        self._insight_app = None
        self._deepface    = None
        self._mode        = "stub"
        self._dim         = EMBEDDING_DIM
        self._load()

    # ── Init ────────────────────────────────────────────────────────────────────

    def _load(self):
        # 1. insightface
        try:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name="buffalo_sc", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            self._insight_app = app
            self._mode = "insightface"
            self._dim  = 512
            logger.info("[ArcFaceEmbedder] insightface ArcFace 512-d loaded")
            return
        except Exception as e:
            logger.warning(f"[ArcFaceEmbedder] insightface unavailable: {e}")

        # 2. deepface ArcFace
        try:
            from deepface import DeepFace
            self._deepface = DeepFace
            self._mode = "deepface_arcface"
            self._dim  = 512
            logger.info("[ArcFaceEmbedder] DeepFace ArcFace 512-d loaded")
            return
        except Exception as e:
            logger.warning(f"[ArcFaceEmbedder] deepface ArcFace unavailable: {e}")

        # 3. deepface Facenet512
        try:
            from deepface import DeepFace
            self._deepface = DeepFace
            self._mode = "deepface_facenet512"
            self._dim  = 512
            logger.info("[ArcFaceEmbedder] DeepFace Facenet512 loaded (fallback)")
            return
        except Exception as e:
            logger.error(f"[ArcFaceEmbedder] All models failed: {e} → stub mode")

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def embedding_dim(self) -> int:
        return self._dim

    # ── Public API ──────────────────────────────────────────────────────────────

    def embed(self, face_rgb: np.ndarray) -> Optional[np.ndarray]:
        """
        Compute L2-normalised embedding from a face crop.
        face_rgb : RGB uint8 array, ideally 112×112 (aligned).
        Returns  : float32 ndarray of shape (dim,)  or  None on failure.
        """
        if face_rgb is None or face_rgb.size == 0:
            return None

        if self._mode == "insightface":
            return self._embed_insightface(face_rgb)
        if self._mode in ("deepface_arcface", "deepface_facenet512"):
            return self._embed_deepface(face_rgb)
        return self._embed_stub()

    def embed_batch(self, faces: list[np.ndarray]) -> list[Optional[np.ndarray]]:
        """Embed a list of face crops. Returns None for any that fail."""
        return [self.embed(f) for f in faces]

    @staticmethod
    def normalize(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    # ── Backends ────────────────────────────────────────────────────────────────

    def _embed_insightface(self, face_rgb: np.ndarray) -> Optional[np.ndarray]:
        try:
            import cv2
            bgr   = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR)
            faces = self._insight_app.get(bgr)
            if not faces:
                return None
            best = max(faces, key=lambda f: f.det_score)
            if best.embedding is None:
                return None
            return self.normalize(best.embedding.astype(np.float32))
        except Exception as e:
            logger.debug(f"[insightface embed] {e}")
            return None

    def _embed_deepface(self, face_rgb: np.ndarray) -> Optional[np.ndarray]:
        import cv2, tempfile, os
        try:
            bgr = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR)
            fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            try:
                cv2.imwrite(tmp_path, bgr)
                model = "ArcFace" if "arcface" in self._mode else "Facenet512"
                result = self._deepface.represent(
                    img_path=tmp_path,
                    model_name=model,
                    detector_backend="skip",   # already aligned/cropped
                    enforce_detection=False,
                    align=False,
                )
                if not result:
                    return None
                emb = np.array(result[0]["embedding"], dtype=np.float32)
                return self.normalize(emb)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except Exception as e:
            logger.debug(f"[deepface embed] {e}")
            return None

    def _embed_stub(self) -> np.ndarray:
        """Random normalised vector — for demo / CI only."""
        v = np.random.randn(self._dim).astype(np.float32)
        return self.normalize(v)
