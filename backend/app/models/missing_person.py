"""
models/missing_person.py
MissingPersons table — records of reported missing individuals.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base


class MissingPerson(Base):
    __tablename__ = "missing_persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    embedding_path = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="missing")  # missing | found

    reported_by = Column(Integer, ForeignKey("complainants.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    complainant = relationship("Complainant", backref="missing_persons", lazy="joined")
    creator = relationship("User", backref="created_persons", lazy="joined")

    def __repr__(self):
        return f"<MissingPerson id={self.id} name={self.name} status={self.status}>"
