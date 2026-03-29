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
    images: list[UploadFile] = None,
) -> MissingPerson:
    """Create a new missing person record, optionally with multiple face images & unified embedding."""
    image_path_str = None
    embedding_path_str = None

    if images:
        image_paths = []
        embeddings = []
        import numpy as np

        for img in images:
            if not img.filename:
                continue
            saved_path = save_image(img)
            image_paths.append(saved_path)
            # Generate face embedding
            embedding = encoder.encode(saved_path)
            if embedding:
                embeddings.append(embedding)
                
        if image_paths:
            image_path_str = ",".join(image_paths)
            
        if embeddings:
            # Average embeddings
            arrs = np.array(embeddings)
            avg_emb = np.mean(arrs, axis=0)
            norm = np.linalg.norm(avg_emb)
            if norm > 0:
                avg_emb = avg_emb / norm
            final_embedding = avg_emb.tolist()
            
            emb_file = EMBEDDINGS_DIR / f"emb_{name.replace(' ', '_')}_{created_by}.json"
            encoder.save_embedding(final_embedding, str(emb_file))
            embedding_path_str = str(emb_file)

    person = MissingPerson(
        name=name,
        age=age,
        gender=gender,
        description=description,
        image_path=image_path_str,
        embedding_path=embedding_path_str,
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
