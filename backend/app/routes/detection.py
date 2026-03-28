"""
routes/detection.py
Detection endpoints — upload video, run detection, get results.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.services.video_service import save_uploaded_video, get_video_info
from app.services.face_service import run_detection_on_video, get_detection_results
from app.utils.helpers import success_response, error_response
from app.config import MAX_VIDEO_SIZE_MB

router = APIRouter(prefix="/api", tags=["Detection"])


# ── POST /upload-video ────────────────────────────────────────────────────────

@router.post("/upload-video")
def upload_video(
    video: UploadFile = File(...),
    camera_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload a CCTV video file for later detection processing."""
    if not video.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("No video file provided"),
        )

    allowed_ext = (".mp4", ".avi", ".mov", ".mkv", ".wmv")
    ext = "." + video.filename.rsplit(".", 1)[-1].lower() if "." in video.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(f"Unsupported format. Allowed: {', '.join(allowed_ext)}"),
        )

    video_path = save_uploaded_video(video)
    info = get_video_info(video_path)

    return success_response("Video uploaded successfully", data={
        "video_path": video_path,
        "camera_id": camera_id,
        **info,
    })


# ── POST /run-detection ──────────────────────────────────────────────────────

@router.post("/run-detection")
def run_detection(
    video_path: str = Form(...),
    camera_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Run face detection on a previously uploaded video.
    Compares detected faces against stored missing person embeddings.
    """
    try:
        results = run_detection_on_video(db, video_path, camera_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(str(e)),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(f"Detection failed: {str(e)}"),
        )

    if not results:
        return success_response("Detection complete — no matches found", data=[])

    return success_response(
        f"Detection complete — {len(results)} match(es) found",
        data=results,
    )


# ── GET /results ──────────────────────────────────────────────────────────────

@router.get("/results")
def get_results(
    person_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Retrieve detection results/logs, optionally filtered by person_id."""
    results = get_detection_results(db, person_id)
    return success_response(f"{len(results)} result(s) found", data=results)
