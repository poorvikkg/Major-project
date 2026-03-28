"""
models/detection_log.py
DetectionLogs table — results from face matching against CCTV footage.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class DetectionLog(Base):
    __tablename__ = "detection_logs"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("missing_persons.id"), nullable=False)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    confidence_score = Column(Float, nullable=False)
    image_snapshot_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    person = relationship("MissingPerson", backref="detections", lazy="joined")
    camera = relationship("Camera", backref="detection_logs", lazy="joined")

    def __repr__(self):
        return f"<DetectionLog id={self.id} person_id={self.person_id} confidence={self.confidence_score}>"
