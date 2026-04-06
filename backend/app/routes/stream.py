"""
routes/stream.py
Real-time pipeline control + result polling endpoints.

Endpoints
─────────
  POST /api/pipeline/start        — start pipeline (loads FAISS from DB)
  POST /api/pipeline/stop         — stop pipeline
  GET  /api/pipeline/status       — pipeline status / metrics
  GET  /api/pipeline/results      — poll latest recognition results
  POST /api/pipeline/reload-index — hot-reload FAISS without restart
  POST /api/pipeline/search       — one-shot image search (base64)
  POST /api/pipeline/clear        — clear result cache
"""
from __future__ import annotations
import base64
import time
import logging
import numpy as np
import cv2

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database                 import get_db
from app.middleware.auth_middleware import get_current_user
from app.pipeline                 import PipelineManager, FaissIndex, pipeline_state
from app.pipeline.initializer     import load_embeddings_into_faiss
from app.pipeline.face_detector   import RetinaFaceDetector
from app.pipeline.face_embedder   import ArcFaceEmbedder
from app.utils.helpers            import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pipeline", tags=["Real-time Pipeline"])

# Module-level singletons (one FAISS index, one pipeline manager)
_faiss_index: FaissIndex                  = FaissIndex()
_pipeline:    PipelineManager | None      = None


# ── POST /start ──────────────────────────────────────────────────────────────

@router.post("/start")
def start_pipeline(
    source:  str = Query("0",  description="0=webcam | RTSP URL | video file path"),
    fps:     int = Query(5,    ge=1, le=30,  description="Target processing FPS"),
    workers: int = Query(2,    ge=1, le=8,   description="Worker thread count"),
    db:      Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Start the real-time face recognition pipeline."""
    global _pipeline, _faiss_index

    if _pipeline and _pipeline.is_running:
        return success_response("Pipeline already running", data=pipeline_state.get_status())

    # Load FAISS from DB
    count = load_embeddings_into_faiss(db, _faiss_index)
    logger.info(f"[/pipeline/start] Loaded {count} embeddings into FAISS")

    cam: str | int = int(source) if source.strip().isdigit() else source
    _pipeline = PipelineManager(
        faiss_index=_faiss_index,
        source=cam,
        target_fps=fps,
        num_workers=workers,
    )
    try:
        _pipeline.start()
    except Exception as e:
        pipeline_state.set_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(f"Pipeline start failed: {e}"),
        )

    return success_response("Pipeline started", data={
        **pipeline_state.get_status(),
        "embeddings_loaded": count,
    })


# ── POST /stop ────────────────────────────────────────────────────────────────

@router.post("/stop")
def stop_pipeline(current_user: dict = Depends(get_current_user)):
    """Stop the running pipeline."""
    global _pipeline
    if _pipeline:
        _pipeline.stop()
        _pipeline = None
    return success_response("Pipeline stopped", data=pipeline_state.get_status())


# ── GET /status ───────────────────────────────────────────────────────────────

@router.get("/status")
def get_status():
    """Current pipeline metrics (FPS, frame count, running state, errors)."""
    return success_response("Pipeline status", data=pipeline_state.get_status())


# ── GET /results ──────────────────────────────────────────────────────────────

@router.get("/results")
def get_results(
    limit: int   = Query(20,  ge=1, le=100),
    since: float = Query(0.0, description="Unix timestamp — only results after this"),
):
    """
    Poll latest recognition results.
    Frontend should call this every 1-2 s, passing the last `timestamp` as `since`.

    Example response:
    {
      "status": "success",
      "data": {
        "results": [
          {
            "person_id":     42,
            "name":          "Ravi Kumar",
            "similarity":    0.9123,
            "confidence":    91.23,
            "bbox":          [120, 80, 160, 200],
            "frame_index":   317,
            "timestamp":     1712345678.45,
            "snapshot_path": "data/outputs/pl_42_a1b2c3d4.jpg",
            "source":        "0"
          }
        ],
        "count":       1,
        "server_time": 1712345680.12
      }
    }
    """
    results = pipeline_state.get_latest_results(limit=limit, since=since)
    return success_response(f"{len(results)} result(s)", data={
        "results":     results,
        "count":       len(results),
        "server_time": time.time(),
    })


# ── POST /reload-index ────────────────────────────────────────────────────────

@router.post("/reload-index")
def reload_index(
    db:           Session = Depends(get_db),
    current_user: dict    = Depends(get_current_user),
):
    """Hot-reload the FAISS index from DB without stopping the pipeline."""
    count = load_embeddings_into_faiss(db, _faiss_index)
    return success_response("FAISS index reloaded", data={"embeddings_loaded": count})


# ── POST /search ──────────────────────────────────────────────────────────────

@router.post("/search")
def search_face(
    payload:      dict    = Body(..., example={"image_base64": "<base64 string>"}),
    db:           Session = Depends(get_db),
    current_user: dict    = Depends(get_current_user),
):
    """
    One-shot face search from a base64-encoded image.
    Useful for testing without the live pipeline.

    Expected body: { "image_base64": "..." }
    """
    b64 = payload.get("image_base64", "")
    if not b64:
        raise HTTPException(status_code=400, detail=error_response("image_base64 required"))

    # Decode image
    try:
        raw = base64.b64decode(b64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("imdecode returned None")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    except Exception as e:
        raise HTTPException(status_code=400, detail=error_response(f"Image decode failed: {e}"))

    detector = RetinaFaceDetector()
    embedder = ArcFaceEmbedder()

    detections = detector.detect_and_align(rgb)
    if not detections:
        return success_response("No faces detected", data={"matches": []})

    all_matches = []
    for det in detections:
        if det.aligned_face is None:
            continue
        emb = embedder.embed(det.aligned_face)
        if emb is None:
            continue
        top = _faiss_index.search(emb, top_k=3)
        all_matches.append({
            "bbox":       list(det.bbox),
            "confidence": det.confidence,
            "matches":    top,
        })

    return success_response(
        f"{len(all_matches)} face(s) processed",
        data={"matches": all_matches},
    )


# ── POST /clear ───────────────────────────────────────────────────────────────

@router.post("/clear")
def clear_results(current_user: dict = Depends(get_current_user)):
    """Clear the in-memory recognition result cache."""
    pipeline_state.clear_results()
    return success_response("Result cache cleared")
