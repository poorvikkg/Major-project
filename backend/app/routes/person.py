"""
routes/person.py
Missing Person CRUD endpoints — full FIR-level data capture.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.middleware.auth_middleware import require_admin
from app.services.person_service import (
    add_person, get_all_persons, get_person_by_id,
    update_person, delete_person, _person_to_dict,
)
from app.utils.helpers import success_response, error_response

router = APIRouter(prefix="/api", tags=["Missing Persons"])


# ── POST /add-person (admin only) ────────────────────────────────────────────

@router.post("/add-person")
def create_person(
    # A - Personal Details
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    nickname: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    height: Optional[str] = Form(None),
    weight: Optional[str] = Form(None),
    complexion: Optional[str] = Form(None),
    blood_group: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    # B - Physical Identification
    identification_marks: Optional[str] = Form(None),
    face_shape: Optional[str] = Form(None),
    hair_color: Optional[str] = Form(None),
    eye_color: Optional[str] = Form(None),
    beard_mustache: Optional[str] = Form(None),
    has_disability: Optional[bool] = Form(False),
    disability_details: Optional[str] = Form(None),
    # C - Last Seen Details
    last_seen_location: Optional[str] = Form(None),
    last_seen_date: Optional[str] = Form(None),
    last_seen_time: Optional[str] = Form(None),
    last_seen_wearing: Optional[str] = Form(None),
    accompanied_by: Optional[str] = Form(None),
    suspected_location: Optional[str] = Form(None),
    # D - Additional Information
    occupation: Optional[str] = Form(None),
    habits: Optional[str] = Form(None),
    languages_known: Optional[str] = Form(None),
    medical_conditions: Optional[str] = Form(None),
    behavioral_notes: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    # E - Complainant Details (inline)
    complainant_name: Optional[str] = Form(None),
    complainant_phone: Optional[str] = Form(None),
    complainant_alt_phone: Optional[str] = Form(None),
    complainant_email: Optional[str] = Form(None),
    complainant_address: Optional[str] = Form(None),
    complainant_relation: Optional[str] = Form(None),
    reported_by: Optional[int] = Form(None),
    # F - Images
    images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Add a new missing person record with full FIR-level details."""
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
        name=name, age=age, gender=gender.lower(),
        nickname=nickname, date_of_birth=date_of_birth,
        height=height, weight=weight, complexion=complexion,
        blood_group=blood_group, nationality=nationality,
        identification_marks=identification_marks, face_shape=face_shape,
        hair_color=hair_color, eye_color=eye_color, beard_mustache=beard_mustache,
        has_disability=has_disability or False,
        disability_details=disability_details,
        last_seen_location=last_seen_location, last_seen_date=last_seen_date,
        last_seen_time=last_seen_time, last_seen_wearing=last_seen_wearing,
        accompanied_by=accompanied_by, suspected_location=suspected_location,
        occupation=occupation, habits=habits, languages_known=languages_known,
        medical_conditions=medical_conditions, behavioral_notes=behavioral_notes,
        description=description,
        complainant_name=complainant_name, complainant_phone=complainant_phone,
        complainant_alt_phone=complainant_alt_phone,
        complainant_email=complainant_email, complainant_address=complainant_address,
        complainant_relation=complainant_relation,
        reported_by=reported_by,
        created_by=int(current_user["sub"]),
        images=images,
    )

    return success_response("Missing person added successfully", data=_person_to_dict(person, include_complainant=True))


# ── GET /persons ──────────────────────────────────────────────────────────────

@router.get("/persons")
def list_persons(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all missing persons, optionally filtered by status."""
    persons = get_all_persons(db, status_filter)
    data = [_person_to_dict(p) for p in persons]
    return success_response("Persons retrieved", data=data)


# ── GET /person/{id} ─────────────────────────────────────────────────────────

@router.get("/person/{person_id}")
def get_person(person_id: int, db: Session = Depends(get_db)):
    """Get full details of a specific missing person by ID."""
    person = get_person_by_id(db, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Person not found"),
        )
    return success_response("Person found", data=_person_to_dict(person, include_complainant=True))


# ── PUT /update-person/{id} (admin only) ─────────────────────────────────────

@router.put("/update-person/{person_id}")
def edit_person(
    person_id: int,
    name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    status_val: Optional[str] = Form(None, alias="status"),
    last_seen_location: Optional[str] = Form(None),
    last_seen_date: Optional[str] = Form(None),
    last_seen_wearing: Optional[str] = Form(None),
    suspected_location: Optional[str] = Form(None),
    behavioral_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Update key fields on an existing missing person (admin only)."""
    kwargs = {}
    for field, val in [
        ("name", name), ("age", age),
        ("last_seen_location", last_seen_location),
        ("last_seen_date", last_seen_date),
        ("last_seen_wearing", last_seen_wearing),
        ("suspected_location", suspected_location),
        ("behavioral_notes", behavioral_notes),
    ]:
        if val is not None:
            kwargs[field] = val
    if gender is not None:
        kwargs["gender"] = gender.lower()
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
    return success_response("Person updated", data=_person_to_dict(person))


# ── DELETE /delete-person/{id} (admin only) ──────────────────────────────────

@router.delete("/delete-person/{person_id}")
def remove_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Delete a missing person record and associated images (admin only)."""
    deleted = delete_person(db, person_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Person not found"),
        )
    return success_response("Person deleted successfully")