"""
routes/complainant.py
POST /add-complainant — register a person reporting a missing individual.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complainant import Complainant
from app.utils.helpers import success_response, error_response

router = APIRouter(prefix="/api", tags=["Complainants"])


class ComplainantRequest(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    relation_to_person: str


@router.post("/add-complainant")
def add_complainant(body: ComplainantRequest, db: Session = Depends(get_db)):
    """Register a new complainant (person reporting a missing person)."""
    if not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Name is required"),
        )
    if not body.phone_number.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Phone number is required"),
        )

    complainant = Complainant(
        name=body.name.strip(),
        phone_number=body.phone_number.strip(),
        email=body.email,
        address=body.address,
        relation_to_person=body.relation_to_person.strip(),
    )
    db.add(complainant)
    db.commit()
    db.refresh(complainant)

    return success_response("Complainant registered", data={
        "id": complainant.id,
        "name": complainant.name,
        "phone_number": complainant.phone_number,
        "relation_to_person": complainant.relation_to_person,
        "created_at": complainant.created_at.isoformat() if complainant.created_at else None,
    })


@router.get("/complainants")
def list_complainants(db: Session = Depends(get_db)):
    """List all complainants."""
    complainants = db.query(Complainant).order_by(Complainant.created_at.desc()).all()
    data = [
        {
            "id": c.id,
            "name": c.name,
            "phone_number": c.phone_number,
            "email": c.email,
            "address": c.address,
            "relation_to_person": c.relation_to_person,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in complainants
    ]
    return success_response("Complainants retrieved", data=data)
