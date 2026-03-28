"""
routes/camera.py
Camera management endpoints — CRUD for CCTV camera sources.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.models.camera import Camera
from app.utils.helpers import success_response, error_response

router = APIRouter(prefix="/api", tags=["Cameras"])


class CameraRequest(BaseModel):
    location: str
    stream_url: Optional[str] = None
    description: Optional[str] = None


@router.post("/cameras")
def add_camera(
    body: CameraRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Register a new CCTV camera (admin only)."""
    camera = Camera(
        location=body.location.strip(),
        stream_url=body.stream_url,
        description=body.description,
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)

    return success_response("Camera added", data={
        "id": camera.id,
        "location": camera.location,
        "stream_url": camera.stream_url,
        "created_at": camera.created_at.isoformat() if camera.created_at else None,
    })


@router.get("/cameras")
def list_cameras(db: Session = Depends(get_db)):
    """List all registered cameras."""
    cameras = db.query(Camera).order_by(Camera.created_at.desc()).all()
    data = [
        {
            "id": c.id,
            "location": c.location,
            "stream_url": c.stream_url,
            "description": c.description,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in cameras
    ]
    return success_response("Cameras retrieved", data=data)


@router.delete("/cameras/{camera_id}")
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Delete a camera (admin only)."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Camera not found"),
        )
    db.delete(camera)
    db.commit()
    return success_response("Camera deleted")
