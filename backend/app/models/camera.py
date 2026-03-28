"""
models/camera.py
Cameras table — registered CCTV camera sources.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database.db import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255), nullable=False)
    stream_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Camera id={self.id} location={self.location}>"
