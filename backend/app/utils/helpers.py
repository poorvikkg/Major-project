"""
utils/helpers.py
Shared utility functions — password hashing, file I/O, response builders.
"""
from __future__ import annotations
import hashlib
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone
from fastapi import UploadFile

from app.config import IMAGES_DIR, VIDEOS_DIR, OUTPUTS_DIR


# ── Password hashing (SHA-256 + salt) ────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored salt$hash string."""
    if "$" not in stored_hash:
        return False
    salt, hashed = stored_hash.split("$", 1)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed


# ── File helpers ──────────────────────────────────────────────────────────────

def save_upload_file(upload: UploadFile, dest_dir: Path, prefix: str = "") -> str:
    """Save an UploadFile to dest_dir and return the relative path string."""
    ext = Path(upload.filename or "file").suffix or ".bin"
    filename = f"{prefix}{uuid.uuid4().hex}{ext}"
    filepath = dest_dir / filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(filepath)


def save_image(upload: UploadFile) -> str:
    """Save an uploaded image to /data/images/."""
    return save_upload_file(upload, IMAGES_DIR, prefix="img_")


def save_video(upload: UploadFile) -> str:
    """Save an uploaded video to /data/videos/."""
    return save_upload_file(upload, VIDEOS_DIR, prefix="vid_")


def save_snapshot(frame, filename: str | None = None) -> str:
    """Save a CV2 frame as a JPEG snapshot to /data/outputs/."""
    import cv2
    if filename is None:
        filename = f"snap_{uuid.uuid4().hex}.jpg"
    filepath = OUTPUTS_DIR / filename
    cv2.imwrite(str(filepath), frame)
    return str(filepath)


# ── Response builders ─────────────────────────────────────────────────────────

def success_response(message: str, data=None, status: str = "success"):
    """Standard success JSON response."""
    response = {"status": status, "message": message}
    if data is not None:
        response["data"] = data
    return response


def error_response(message: str, status: str = "error"):
    """Standard error JSON response."""
    return {"status": status, "message": message}


# ── Misc ──────────────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)
