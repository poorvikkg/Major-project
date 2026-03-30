"""
models/complainant.py
Complainants table — people who report a missing person.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database.db import Base


class Complainant(Base):
    __tablename__ = "complainants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    phone_number = Column(String(20), nullable=False)
    alternate_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    relation_to_person = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Complainant id={self.id} name={self.name}>"
