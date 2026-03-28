"""
routes/person.py
Missing Person CRUD endpoints — some protected by admin auth.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import require_admin, get_current_user
from app.services.person_service import (
    add_person, get_all_persons, get_person_by_id, update_person, delete_person,
)
from app.utils.helpers import success_response, error_response

router = APIRouter(prefix="/api", tags=["Missing Persons"])


# ── POST /add-person (admin only) ────────────────────────────────────────────

@router.post("/add-person")
def create_person(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    description: str = Form(""),
    reported_by: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Add a new missing person record with optional face image."""
    if age < 0 or age > 150:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Age must be between 0 and 150"),
        )
    if gender.lower() not in ("male", "female", "other"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Gender must be male, female, or other"),
        )

    person = add_person(
        db=db,
        name=name,
        age=age,
        gender=gender.lower(),
        description=description,
        created_by=int(current_user["sub"]),
        reported_by=reported_by,
        image=image,
    )

    return success_response("Missing person added successfully", data={
        "id": person.id,
        "name": person.name,
        "age": person.age,
        "gender": person.gender,
        "status": person.status,
        "image_path": person.image_path,
        "embedding_path": person.embedding_path,
        "created_at": person.created_at.isoformat() if person.created_at else None,
    })


# ── GET /persons ──────────────────────────────────────────────────────────────

@router.get("/persons")
def list_persons(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all missing persons, optionally filtered by status."""
    persons = get_all_persons(db, status_filter)
    data = [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "description": p.description,
            "status": p.status,
            "image_path": p.image_path,
            "reported_by": p.reported_by,
            "created_by": p.created_by,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in persons
    ]
    return success_response("Persons retrieved", data=data)


# ── GET /person/{id} ─────────────────────────────────────────────────────────

@router.get("/person/{person_id}")
def get_person(person_id: int, db: Session = Depends(get_db)):
    """Get details of a specific missing person by ID."""
    person = get_person_by_id(db, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Person not found"),
        )
    return success_response("Person found", data={
        "id": person.id,
        "name": person.name,
        "age": person.age,
        "gender": person.gender,
        "description": person.description,
        "status": person.status,
        "image_path": person.image_path,
        "embedding_path": person.embedding_path,
        "reported_by": person.reported_by,
        "created_by": person.created_by,
        "created_at": person.created_at.isoformat() if person.created_at else None,
    })


# ── PUT /update-person/{id} (admin only) ─────────────────────────────────────

@router.put("/update-person/{person_id}")
def edit_person(
    person_id: int,
    name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    status_val: Optional[str] = Form(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Update details of an existing missing person (admin only)."""
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if age is not None:
        kwargs["age"] = age
    if gender is not None:
        kwargs["gender"] = gender.lower()
    if description is not None:
        kwargs["description"] = description
    if status_val is not None:
        if status_val not in ("missing", "found"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response("Status must be 'missing' or 'found'"),
            )
        kwargs["status"] = status_val

    person = update_person(db, person_id, **kwargs)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Person not found"),
        )
    return success_response("Person updated", data={
        "id": person.id,
        "name": person.name,
        "status": person.status,
    })


# ── DELETE /delete-person/{id} (admin only) ──────────────────────────────────

@router.delete("/delete-person/{person_id}")
def remove_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Delete a missing person record (admin only)."""
    deleted = delete_person(db, person_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Person not found"),
        )
    return success_response("Person deleted successfully")