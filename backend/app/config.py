"""
Application configuration — reads from environment variables with sensible defaults.
"""
import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
OUTPUTS_DIR = DATA_DIR / "outputs"
VIDEOS_DIR = DATA_DIR / "videos"

# Ensure directories exist
for d in (IMAGES_DIR, EMBEDDINGS_DIR, OUTPUTS_DIR, VIDEOS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "major_project")
DB_USER = os.getenv("DB_USER", "poorvik")
DB_PASS = os.getenv("DB_PASS", "poorvik123")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ── JWT / Auth ────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "mpds-super-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MIN", "120"))

# ── Face Recognition ─────────────────────────────────────────────────────────
FACENET_MODEL = os.getenv("FACENET_MODEL", "Facenet")
DETECTOR_BACKEND = os.getenv("DETECTOR_BACKEND", "opencv")
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.65"))

# ── Video Processing ─────────────────────────────────────────────────────────
FRAME_SKIP = int(os.getenv("FRAME_SKIP", "10"))           # process every Nth frame
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))
