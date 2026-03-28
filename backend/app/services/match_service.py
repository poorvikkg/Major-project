"""
services/match_service.py
Thin wrapper around FaceMatcher for use by routes.
"""
from __future__ import annotations
from app.core.face_encoder import FaceEncoder
from app.core.face_matcher import FaceMatcher

encoder = FaceEncoder()
matcher = FaceMatcher()


def compare_two_images(image_path_1: str, image_path_2: str) -> dict:
    """Compare faces in two images and return similarity score."""
    emb1 = encoder.encode(image_path_1)
    emb2 = encoder.encode(image_path_2)

    if emb1 is None or emb2 is None:
        return {
            "match": False,
            "similarity": 0.0,
            "message": "Could not detect face in one or both images",
        }

    similarity = matcher.cosine_similarity(emb1, emb2)
    return {
        "match": matcher.is_match(similarity),
        "similarity": round(similarity * 100, 2),
        "message": "Match found" if matcher.is_match(similarity) else "No match",
    }
