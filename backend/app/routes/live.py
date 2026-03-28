"""
routes/live.py
Live CCTV streaming endpoint — returns MJPEG stream.
"""
from __future__ import annotations
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.services.video_service import generate_live_frames

router = APIRouter(prefix="/api", tags=["Live CCTV"])


@router.get("/live-stream")
def live_stream(
    source: str = Query("0", description="Camera source: 0 for webcam, RTSP URL, or video file path"),
):
    """
    Stream live CCTV feed as MJPEG.

    - source=0  →  default webcam
    - source=rtsp://...  →  IP camera
    - source=/path/to/video.mp4  →  video file playback

    View in browser at: http://localhost:8000/api/live-stream?source=0
    """
    # Convert "0" to integer for webcam
    cam_source: str | int = source
    if source.isdigit():
        cam_source = int(source)

    return StreamingResponse(
        generate_live_frames(cam_source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
