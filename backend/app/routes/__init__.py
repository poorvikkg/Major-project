from app.routes.auth import router as auth_router
from app.routes.person import router as person_router
from app.routes.complainant import router as complainant_router
from app.routes.detection import router as detection_router
from app.routes.upload import router as upload_router
from app.routes.live import router as live_router
from app.routes.camera import router as camera_router

__all__ = [
    "auth_router",
    "person_router",
    "complainant_router",
    "detection_router",
    "upload_router",
    "live_router",
    "camera_router",
]
