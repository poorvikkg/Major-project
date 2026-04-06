"""
routes/rtsp.py
Real-time CCTV RTSP streaming endpoints.

POST /api/stream/start     — accept RTSP URL, start annotated stream
POST /api/stream/stop      — stop the active stream
GET  /api/stream/video_feed — MJPEG stream with bounding boxes + labels
GET  /api/stream/results   — latest per-frame detection results (JSON)
GET  /api/stream/status    — stream health / pipeline status
"""
from __future__ import annotations
import time
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database                  import get_db
from app.middleware.auth_middleware import get_current_user
from app.pipeline.shared_state     import pipeline_state
from app.pipeline.initializer      import load_embeddings_into_faiss
from app.routes.stream             import _faiss_index
from app.services.rtsp_service     import stream_registry
from app.utils.helpers             import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stream", tags=["RTSP Stream"])


# ── Request schema ────────────────────────────────────────────────────────────

class StartStreamRequest(BaseModel):
    rtsp_url: str
    fps:      int = 5
    reload_index: bool = True


# ── POST /start ───────────────────────────────────────────────────────────────

@router.post("/start")
def start_stream(
    body: StartStreamRequest,
    db:   Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Start (or restart) the annotated CCTV stream.

    Body:
      rtsp_url     — RTSP URL, e.g. rtsp://admin:pass@192.168.1.100:554/stream1
                     or  "0"  for the local webcam
      fps          — target processing FPS  (default 5)
      reload_index — if true, refreshes FAISS from DB before starting

    RTSP is never exposed to the frontend; all processing is server-side.
    """
    url = body.rtsp_url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("rtsp_url is required"),
        )

    # Reload FAISS so newly registered persons are included
    if body.reload_index:
        count = load_embeddings_into_faiss(db, _faiss_index)
        logger.info(f"[/stream/start] FAISS reloaded: {count} embeddings")
    else:
        count = _faiss_index.size

    # Start the stream (non-blocking)
    err = stream_registry.start(source=url, faiss_index=_faiss_index, fps=body.fps)
    if err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_response(f"Stream connection failed: {err}"),
        )

    return success_response("Stream started", data={
        "source":            url,
        "fps":               body.fps,
        "embeddings_loaded": count,
        "video_feed_url":    "/api/stream/video_feed",
        "results_url":       "/api/stream/results",
    })


# ── POST /stop ────────────────────────────────────────────────────────────────

@router.post("/stop")
def stop_stream(current_user: dict = Depends(get_current_user)):
    """Stop the active CCTV stream."""
    stream_registry.stop()
    return success_response("Stream stopped", data=pipeline_state.get_status())


# ── GET /video_feed ───────────────────────────────────────────────────────────

@router.get("/video_feed")
def video_feed():
    """
    MJPEG stream of annotated frames.
    Each frame has bounding boxes, name labels, and confidence scores overlaid.

    Usage in frontend:
      <img src="http://localhost:8000/api/stream/video_feed" />

    No auth required so the browser <img> tag can load it directly.
    """
    if not stream_registry.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("No active stream. Call POST /api/stream/start first."),
        )

    return StreamingResponse(
        stream_registry.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ── GET /results ──────────────────────────────────────────────────────────────

@router.get("/results")
def get_results(
    limit: int   = Query(20, ge=1, le=100),
    since: float = Query(0.0, description="Unix timestamp — only results after this"),
):
    """
    Latest recognition results from the active stream.
    Poll every 1-2 s from the frontend; pass last timestamp as `since`.

    Example response item:
    {
      "person_id":  42,
      "name":       "Ravi Kumar",
      "confidence": 91.2,
      "similarity": 0.912,
      "bbox":       [120, 80, 160, 200],
      "frame":      317,
      "timestamp":  1712345678.45
    }
    """
    frame_results  = stream_registry.latest_results()
    cached_results = pipeline_state.get_latest_results(limit=limit, since=since)

    return success_response(f"{len(cached_results)} result(s)", data={
        "frame_results":  frame_results[:limit],
        "history":        cached_results,
        "count":          len(cached_results),
        "server_time":    time.time(),
    })


# ── GET /status ───────────────────────────────────────────────────────────────

@router.get("/status")
def stream_status():
    """Health and metrics for the running stream. No auth required."""
    return success_response("Stream status", data={
        **pipeline_state.get_status(),
        "stream_source":  stream_registry.source,
        "stream_active":  stream_registry.is_running,
        "faiss_size":     _faiss_index.size,
    })
