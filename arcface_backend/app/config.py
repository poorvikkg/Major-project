import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"

# Face Recognition Settings
MODEL_NAME = "ArcFace"
DISTANCE_METRIC = "cosine"
# DeepFace default threshold for ArcFace with cosine similarity is ~0.68
THRESHOLD = 0.68
