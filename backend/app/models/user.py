"""
models/user.py
Users table — authentication and role management.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin | user
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
