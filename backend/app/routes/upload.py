"""
routes/upload.py
Additional upload endpoint — compare two face images directly.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.middleware.auth_middleware import get_current_user
from app.services.match_service import compare_two_images
from app.utils.helpers import save_image, success_response, error_response

router = APIRouter(prefix="/api", tags=["Upload & Compare"])


@router.post("/compare-faces")
def compare_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload two face images and get a similarity comparison result."""
    for img in (image1, image2):
        if not img.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response("Both image files are required"),
            )

    path1 = save_image(image1)
    path2 = save_image(image2)

    result = compare_two_images(path1, path2)
    return success_response("Comparison complete", data=result)
