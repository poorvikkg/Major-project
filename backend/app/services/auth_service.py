"""
services/auth_service.py
Handles login logic — validates credentials and returns JWT.
"""
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.helpers import verify_password
from app.middleware.auth_middleware import create_access_token


def authenticate_user(db: Session, email: str, password: str) -> dict | None:
    """
    Verify credentials and return a JWT token payload on success.
    Returns None if authentication fails.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }
