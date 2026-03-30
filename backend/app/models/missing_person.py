"""
models/missing_person.py
MissingPersons table — FIR-level records of reported missing individuals.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class MissingPerson(Base):
    __tablename__ = "missing_persons"

    id = Column(Integer, primary_key=True, index=True)

    # ── A. Personal Details ────────────────────────────────────────────────────
    name = Column(String(120), nullable=False)
    nickname = Column(String(120), nullable=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    date_of_birth = Column(String(20), nullable=True)   # YYYY-MM-DD string
    height = Column(String(20), nullable=True)          # e.g. "5ft 8in" or "173cm"
    weight = Column(String(20), nullable=True)          # e.g. "65kg"
    complexion = Column(String(50), nullable=True)
    blood_group = Column(String(10), nullable=True)
    nationality = Column(String(60), nullable=True)

    # ── B. Physical Identification ─────────────────────────────────────────────
    identification_marks = Column(Text, nullable=True)  # scars, tattoos, birthmarks
    face_shape = Column(String(50), nullable=True)
    hair_color = Column(String(50), nullable=True)
    eye_color = Column(String(50), nullable=True)
    beard_mustache = Column(String(100), nullable=True)
    has_disability = Column(Boolean, nullable=True, default=False)
    disability_details = Column(Text, nullable=True)

    # ── C. Last Seen Details ───────────────────────────────────────────────────
    last_seen_location = Column(Text, nullable=True)
    last_seen_date = Column(String(20), nullable=True)
    last_seen_time = Column(String(20), nullable=True)
    last_seen_wearing = Column(Text, nullable=True)
    accompanied_by = Column(Text, nullable=True)
    suspected_location = Column(Text, nullable=True)

    # ── D. Additional Information ──────────────────────────────────────────────
    occupation = Column(String(120), nullable=True)
    habits = Column(Text, nullable=True)          # smoking, drinking, etc.
    languages_known = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    behavioral_notes = Column(Text, nullable=True)

    # ── Legacy / Catch-all ─────────────────────────────────────────────────────
    description = Column(Text, nullable=True)

    # ── Images & Embeddings ────────────────────────────────────────────────────
    image_path = Column(Text, nullable=True)          # comma-separated paths
    embedding_path = Column(String(500), nullable=True)

    # ── Status & Meta ──────────────────────────────────────────────────────────
    status = Column(String(20), nullable=False, default="missing")  # missing | found

    reported_by = Column(Integer, ForeignKey("complainants.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    complainant = relationship("Complainant", backref="missing_persons", lazy="joined")
    creator = relationship("User", backref="created_persons", lazy="joined")
    # Note: DetectionLog defines the reverse side via backref="detections"

    def __repr__(self):
        return f"<MissingPerson id={self.id} name={self.name} status={self.status}>"
