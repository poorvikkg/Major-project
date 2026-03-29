import json
import logging
import os
import tempfile
import numpy as np
from fastapi import UploadFile
from deepface import DeepFace

from app.config import EMBEDDINGS_FILE, MODEL_NAME, THRESHOLD
from app.utils import cosine_similarity

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FaceRecognitionService:
    def __init__(self):
        self.embeddings_db = self._load_db()

    def _load_db(self) -> dict:
        """Load the in-memory dictionary of embeddings from JSON."""
        if EMBEDDINGS_FILE.exists():
            try:
                with open(EMBEDDINGS_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Embeddings file is invalid. Starting fresh.")
        return {}

    def _save_db(self):
        """Persist the in-memory embeddings to JSON."""
        with open(EMBEDDINGS_FILE, "w") as f:
            json.dump(self.embeddings_db, f, indent=4)

    def _get_embedding(self, image_path: str) -> list[float] | None:
        """Extract face embedding using DeepFace ArcFace model."""
        try:
            # DeepFace.represent returns a list of dictionaries (one per face)
            results = DeepFace.represent(
                img_path=image_path,
                model_name=MODEL_NAME,
                enforce_detection=True,
                align=True
            )
            if results and len(results) > 0:
                # Assuming the first detected face is the primary one
                return results[0]["embedding"]
        except ValueError as e:
            logger.error(f"DeepFace encoding error (No face detected): {e}")
        except Exception as e:
            logger.error(f"Unexpected error during encoding: {e}")
        return None

    def register_person(self, name: str, images: list[UploadFile]) -> bool:
        if not images:
            return False

        generated_embeddings = []
        for img_obj in images:
            suffix = os.path.splitext(img_obj.filename)[1] or ".jpg"
            # Save uploaded file to temp image securely
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(img_obj.file.read())
                tmp_path = tmp.name

            embedding = self._get_embedding(tmp_path)
            os.unlink(tmp_path)  # Clean up temp file

            if embedding:
                generated_embeddings.append(embedding)

        if not generated_embeddings:
            return False

        # Average all successful embeddings to create a single robust prototype
        arrs = np.array(generated_embeddings)
        avg_emb = np.mean(arrs, axis=0)
        
        # Normalize the averaged embedding
        norm = np.linalg.norm(avg_emb)
        if norm > 0:
            avg_emb = avg_emb / norm
        
        self.embeddings_db[name] = avg_emb.tolist()
        self._save_db()
        return True

    def verify_person(self, image: UploadFile) -> tuple[str | None, float]:
        """Verify an image and return (person_name, confidence) if matched."""
        if not self.embeddings_db:
            return None, 0.0

        suffix = os.path.splitext(image.filename)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image.file.read())
            tmp_path = tmp.name

        probe_embedding = self._get_embedding(tmp_path)
        os.unlink(tmp_path)

        if not probe_embedding:
            return None, 0.0

        best_match = None
        best_score = -1.0

        for name, stored_emb in self.embeddings_db.items():
            sim = cosine_similarity(probe_embedding, stored_emb)
            if sim > best_score:
                best_score = sim
                best_match = name

        if best_score >= THRESHOLD:
            # We have a match above the strict ArcFace threshold!
            return best_match, best_score
        
        # Even if best_match exists, it didn't pass the similarity threshold
        return None, best_score

# Singleton service instance
face_service = FaceRecognitionService()
