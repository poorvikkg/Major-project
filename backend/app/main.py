"""
main.py
FastAPI application — registers routers, CORS, and startup hooks.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import DATA_DIR
from app.database.operations import init_db, seed_admin
from app.routes import (
    auth_router,
    person_router,
    complainant_router,
    detection_router,
    upload_router,
    live_router,
    camera_router,
)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup: create DB tables and seed admin user."""
    init_db()
    seed_admin()
    yield


# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Missing Person Detection System",
    description="AI-powered CCTV surveillance and face recognition API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow frontend on localhost:5173) ───────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve uploaded files as static (images, outputs, etc.) ────────────────────

app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# ── Register routers ─────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(person_router)
app.include_router(complainant_router)
app.include_router(detection_router)
app.include_router(upload_router)
app.include_router(live_router)
app.include_router(camera_router)


# ── Root health check ────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "success",
        "message": "Missing Person Detection System API is running",
        "docs": "/docs",
    }