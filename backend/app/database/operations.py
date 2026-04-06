"""
database/operations.py
Database initialisation helpers — table creation, seed admin user.
"""
from sqlalchemy.orm import Session
from app.database.db import Base, engine, SessionLocal
from app.models.user import User
from app.utils.helpers import hash_password


def init_db():
    """Create all tables defined by Base metadata."""
    import app.models  # noqa: F401 — ensure all models are imported
    Base.metadata.create_all(bind=engine)
    print("[+] Database tables created")


def seed_admin():
    """Insert default admin user if none exists."""
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@mpds.com").first()
        if not existing:
            admin = User(
                name="Admin User",
                email="admin@mpds.com",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("[+] Default admin seeded (admin@mpds.com / admin123)")
        else:
            print("ℹ️   Admin user already exists")
    finally:
        db.close()
