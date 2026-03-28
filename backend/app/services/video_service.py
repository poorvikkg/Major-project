"""
services/video_service.py
Video upload, frame extraction, and streaming helpers.
"""
from __future__ import annotations
import cv2
from pathlib import Path
from fastapi import UploadFile
from app.utils.helpers import save_video


def save_uploaded_video(upload: UploadFile) -> str:
    """Save uploaded video file and return path."""
    return save_video(upload)


def extract_frames(video_path: str, every_n: int = 30) -> list:
    """
    Extract every Nth frame from a video.
    Returns a list of (frame_index, numpy_frame) tuples.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % every_n == 0:
            frames.append((idx, frame))
        idx += 1

    cap.release()
    return frames


def get_video_info(video_path: str) -> dict:
    """Return basic metadata about a video file."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Cannot open video"}

    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration_sec": round(
            int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / max(cap.get(cv2.CAP_PROP_FPS), 1), 2
        ),
    }
    cap.release()
    return info


def generate_live_frames(source: str | int = 0):
    """
    Generator that yields JPEG-encoded frames from a camera source.
    Used for MJPEG streaming.  source can be:
      - 0  (default webcam)
      - RTSP URL string
      - video file path
    """
    cap = cv2.VideoCapture(source)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
    finally:
        cap.release()
