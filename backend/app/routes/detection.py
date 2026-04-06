"""
routes/detection.py
Detection endpoints — upload video, run detection, get results.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, SessionLocal
from app.middleware.auth_middleware import get_current_user
from app.services.video_service import save_uploaded_video, get_video_info
from app.services.face_service import run_detection_on_video, get_detection_results
from app.models.detection_log import DetectionLog
from app.utils.helpers import success_response, error_response
from pydantic import BaseModel

class StatusUpdate(BaseModel):
    status: str
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

active_tasks = {}

@router.post("/run-detection")
def run_detection(
    background_tasks: BackgroundTasks,
    video_path: str = Form(...),
    camera_id: Optional[int] = Form(None),
    target_person_id: Optional[int] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Run face detection on a previously uploaded video.
    Compares detected faces against stored missing person embeddings.
    """
    import logging
    import uuid
    from datetime import datetime
    logger = logging.getLogger(__name__)
    
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {
        "id": task_id,
        "video_path": video_path,
        "status": "processing",
        "started_at": datetime.now().isoformat()
    }

    def process_video_bg(tid: str):
        db_bg = SessionLocal()
        try:
            logger.info(f"Starting background detection for {video_path}")
            run_detection_on_video(db_bg, video_path, camera_id, target_person_id)
            logger.info("Background detection completed successfully")
        except Exception as e:
            logger.error(f"Background detection failed: {e}")
        finally:
            active_tasks.pop(tid, None)
            db_bg.close()

    background_tasks.add_task(process_video_bg, task_id)

    return success_response(
        "Detection started in background. Results will appear in the dashboard when ready.",
        data={"task_id": task_id}
    )

@router.get("/active-tasks")
def get_active_tasks(current_user: dict = Depends(get_current_user)):
    """Return a list of currently processing video tasks."""
    return success_response("Active tasks", data=list(active_tasks.values()))

# ── GET /results ──────────────────────────────────────────────────────────────

@router.get("/results")
def get_results(
    person_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve detection results/logs, optionally filtered by person_id."""
    results = get_detection_results(db, person_id)
    return success_response(f"{len(results)} result(s) found", data=results)


@router.patch("/results/{result_id}/status")
def update_result_status(
    result_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update the status of a detection result (e.g., 'confirmed', 'dismissed')."""
    log = db.query(DetectionLog).filter(DetectionLog.id == result_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=error_response("Result not found"))
    
    log.status = data.status
    db.commit()
    return success_response(f"Result {result_id} status updated to {data.status}")


@router.delete("/results/{result_id}")
def delete_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a detection result."""
    log = db.query(DetectionLog).filter(DetectionLog.id == result_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=error_response("Result not found"))
    import os
    if log.image_snapshot_path and os.path.exists(log.image_snapshot_path):
        try:
            os.remove(log.image_snapshot_path)
        except OSError:
            pass
    db.delete(log)
    db.commit()
    return success_response(f"Result {result_id} deleted")
