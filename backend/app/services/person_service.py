"""
services/person_service.py
CRUD operations for missing persons.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.missing_person import MissingPerson
from app.utils.helpers import save_image
from app.config import EMBEDDINGS_DIR
from app.core.face_encoder import FaceEncoder

encoder = FaceEncoder()


def add_person(
    db: Session,
    name: str,
    age: int,
    gender: str,
    description: str,
    created_by: int,
    reported_by: int | None = None,
    image: UploadFile | None = None,
) -> MissingPerson:
    """Create a new missing person record, optionally with face image & embedding."""
    image_path = None
    embedding_path = None

    if image:
        image_path = save_image(image)
        # Generate face embedding
        embedding = encoder.encode(image_path)
        if embedding:
            emb_file = EMBEDDINGS_DIR / f"emb_{name.replace(' ', '_')}_{created_by}.json"
            encoder.save_embedding(embedding, str(emb_file))
            embedding_path = str(emb_file)

    person = MissingPerson(
        name=name,
        age=age,
        gender=gender,
        description=description,
        image_path=image_path,
        embedding_path=embedding_path,
        status="missing",
        reported_by=reported_by,
        created_by=created_by,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def get_all_persons(db: Session, status_filter: str | None = None) -> list[MissingPerson]:
    """Retrieve all missing persons, optionally filtered by status."""
    query = db.query(MissingPerson)
    if status_filter:
        query = query.filter(MissingPerson.status == status_filter)
    return query.order_by(MissingPerson.created_at.desc()).all()


def get_person_by_id(db: Session, person_id: int) -> MissingPerson | None:
    """Get a single missing person by ID."""
    return db.query(MissingPerson).filter(MissingPerson.id == person_id).first()


def update_person(
    db: Session,
    person_id: int,
    **kwargs,
) -> MissingPerson | None:
    """Update fields on an existing missing person."""
    person = db.query(MissingPerson).filter(MissingPerson.id == person_id).first()
    if not person:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(person, key):
            setattr(person, key, value)
    db.commit()
    db.refresh(person)
    return person


def delete_person(db: Session, person_id: int) -> bool:
    """Delete a missing person record. Returns True if deleted."""
    person = db.query(MissingPerson).filter(MissingPerson.id == person_id).first()
    if not person:
        return False
    db.delete(person)
    db.commit()
    return True
