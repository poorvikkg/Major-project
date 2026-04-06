"""
pipeline/config.py
Configurable parameters for the real-time face recognition pipeline.
All values can be overridden via environment variables.
"""
import os
from pathlib import Path

# ── Video Source ──────────────────────────────────────────────────────────────
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")          # 0=webcam, RTSP URL, file

# ── Frame Processing ──────────────────────────────────────────────────────────
TARGET_FPS       = int(os.getenv("PIPELINE_FPS", "5"))       # frames/sec to process
FRAME_WIDTH      = int(os.getenv("FRAME_WIDTH", "640"))
FRAME_HEIGHT     = int(os.getenv("FRAME_HEIGHT", "480"))

# ── Face Detection ────────────────────────────────────────────────────────────
DETECTION_BACKEND     = os.getenv("DETECTION_BACKEND", "retinaface")
MIN_FACE_SIZE         = int(os.getenv("MIN_FACE_SIZE", "40"))    # pixels
DETECTION_CONFIDENCE  = float(os.getenv("DETECTION_CONFIDENCE", "0.85"))

# ── Embedding ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "arcface")
EMBEDDING_DIM   = int(os.getenv("EMBEDDING_DIM", "512"))

# ── FAISS ─────────────────────────────────────────────────────────────────────
FAISS_INDEX_TYPE  = os.getenv("FAISS_INDEX_TYPE", "Flat")   # Flat | IVF
_BASE             = Path(__file__).resolve().parent.parent.parent  # backend/
FAISS_INDEX_PATH  = Path(os.getenv("FAISS_INDEX_PATH", str(_BASE / "data" / "faiss" / "index.bin")))
FAISS_META_PATH   = Path(os.getenv("FAISS_META_PATH",  str(_BASE / "data" / "faiss" / "meta.json")))
FAISS_IVF_NLIST   = int(os.getenv("FAISS_IVF_NLIST", "100"))

# ── Matching ──────────────────────────────────────────────────────────────────
MATCH_THRESHOLD = float(os.getenv("PIPELINE_MATCH_THRESHOLD", "0.65"))
TOP_K           = int(os.getenv("PIPELINE_TOP_K", "3"))

# ── Pipeline Threading ────────────────────────────────────────────────────────
QUEUE_MAXSIZE   = int(os.getenv("PIPELINE_QUEUE_SIZE", "30"))
WORKER_THREADS  = int(os.getenv("PIPELINE_WORKERS", "2"))
RESULT_TTL_SEC  = int(os.getenv("PIPELINE_RESULT_TTL", "60"))   # seconds

# ── Snapshots ─────────────────────────────────────────────────────────────────
SAVE_SNAPSHOTS = os.getenv("SAVE_SNAPSHOTS", "true").lower() == "true"
SNAPSHOT_DIR   = Path(os.getenv("SNAPSHOT_DIR", str(_BASE / "data" / "outputs")))
