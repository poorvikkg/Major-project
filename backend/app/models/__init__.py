"""
models/__init__.py
Import all models so SQLAlchemy registers them with Base.metadata.
"""
from app.models.user import User
from app.models.complainant import Complainant
from app.models.missing_person import MissingPerson
from app.models.camera import Camera
from app.models.detection_log import DetectionLog

__all__ = ["User", "Complainant", "MissingPerson", "Camera", "DetectionLog"]
