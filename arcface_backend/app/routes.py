from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import List
from app.services import face_service

router = APIRouter()

@router.post("/register")
def register_person(
    name: str = Form(..., description="Name of the person to register"),
    images: List[UploadFile] = File(..., description="Multiple reference images")
):
    """
    Accept multiple images of a person and store their unified embedding.
    """
    success = face_service.register_person(name, images)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate embeddings. Ensure faces are clearly visible in the images."
        )
    return {
        "status": "success",
        "message": f"Person '{name}' registered successfully with {len(images)} images."
    }

@router.post("/verify")
def verify_person(
    image: UploadFile = File(..., description="A new image to verify")
):
    """
    Accept a new image and compare with stored embeddings to find a match.
    """
    matched_name, similarity_score = face_service.verify_person(image)
    
    if matched_name:
        return {
            "status": "success",
            "match": True,
            "person_name": matched_name,
            "similarity_score": round(similarity_score, 4)
        }
    else:
        return {
            "status": "success",
            "match": False,
            "person_name": "Unknown",
            "similarity_score": round(similarity_score, 4) if similarity_score > -1.0 else 0.0
        }
