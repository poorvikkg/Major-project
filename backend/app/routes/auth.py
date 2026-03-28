"""
routes/auth.py
POST /login — authenticate and return JWT token.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import authenticate_user
from app.utils.helpers import success_response, error_response

router = APIRouter(prefix="/api", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    result = authenticate_user(db, body.email, body.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("Invalid email or password"),
        )
    return success_response("Login successful", data=result)
