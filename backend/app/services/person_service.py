"""
services/person_service.py
CRUD operations for missing persons — supports per-person image folders
and averaged face embeddings from multiple uploads.
"""
from __future__ import annotations
import shutil
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.missing_person import MissingPerson
from app.models.complainant import Complainant
from app.config import IMAGES_DIR, EMBEDDINGS_DIR
from app.pipeline.face_detector import RetinaFaceDetector
from app.pipeline.face_embedder import ArcFaceEmbedder

pipeline_detector = RetinaFaceDetector()
pipeline_embedder = ArcFaceEmbedder()

# ── helpers ───────────────────────────────────────────────────────────────────

def _save_images_for_person(person_id: int, images: list[UploadFile]) -> list[str]:
    """Save images into /data/images/{person_id}/ and return list of paths."""
    person_dir = IMAGES_DIR / str(person_id)
    person_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for img in images:
        if not img.filename:
            continue
        ext = Path(img.filename).suffix or ".jpg"
        filename = f"img_{uuid.uuid4().hex}{ext}"
        dest = person_dir / filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(img.file, f)
        paths.append(str(dest))
    return paths


def _build_embedding(image_paths: list[str], person_id: int, name: str) -> str | None:
    """Generate averaged + normalised face embedding from image paths."""
    import cv2
    import numpy as np
    import json
    embeddings = []
    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        dets = pipeline_detector.detect_and_align(rgb)
        if dets and dets[0].aligned_face is not None:
            emb = pipeline_embedder.embed(dets[0].aligned_face)
            if emb is not None:
                embeddings.append(emb)
    if not embeddings:
        return None
    arrs = np.array(embeddings)
    avg = np.mean(arrs, axis=0)
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm
    emb_file = EMBEDDINGS_DIR / f"emb_{person_id}_{name.replace(' ', '_')}.json"
    with open(str(emb_file), "w") as f:
        json.dump(avg.tolist(), f)
    return str(emb_file)


def _complainant_to_dict(c: Complainant | None) -> dict | None:
    if c is None:
        return None
    return {
        "id": c.id,
        "name": c.name,
        "phone_number": c.phone_number,
        "alternate_phone": c.alternate_phone,
        "email": c.email,
        "address": c.address,
        "relation_to_person": c.relation_to_person,
    }


def _person_to_dict(p: MissingPerson, include_complainant: bool = False) -> dict:
    d = {
        "id": p.id,
        # A
        "name": p.name,
        "nickname": p.nickname,
        "age": p.age,
        "gender": p.gender,
        "date_of_birth": p.date_of_birth,
        "height": p.height,
        "weight": p.weight,
        "complexion": p.complexion,
        "blood_group": p.blood_group,
        "nationality": p.nationality,
        # B
        "identification_marks": p.identification_marks,
        "face_shape": p.face_shape,
        "hair_color": p.hair_color,
        "eye_color": p.eye_color,
        "beard_mustache": p.beard_mustache,
        "has_disability": p.has_disability,
        "disability_details": p.disability_details,
        # C
        "last_seen_location": p.last_seen_location,
        "last_seen_date": p.last_seen_date,
        "last_seen_time": p.last_seen_time,
        "last_seen_wearing": p.last_seen_wearing,
        "accompanied_by": p.accompanied_by,
        "suspected_location": p.suspected_location,
        # D
        "occupation": p.occupation,
        "habits": p.habits,
        "languages_known": p.languages_known,
        "medical_conditions": p.medical_conditions,
        "behavioral_notes": p.behavioral_notes,
        # Legacy
        "description": p.description,
        # Meta
        "image_path": p.image_path,
        "embedding_path": p.embedding_path,
        "status": p.status,
        "reported_by": p.reported_by,
        "created_by": p.created_by,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
    if include_complainant:
        d["complainant"] = _complainant_to_dict(p.complainant)
    return d


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_person(
    db: Session,
    *,
    # A - Personal
    name: str,
    age: int,
    gender: str,
    nickname: str | None = None,
    date_of_birth: str | None = None,
    height: str | None = None,
    weight: str | None = None,
    complexion: str | None = None,
    blood_group: str | None = None,
    nationality: str | None = None,
    # B - Physical
    identification_marks: str | None = None,
    face_shape: str | None = None,
    hair_color: str | None = None,
    eye_color: str | None = None,
    beard_mustache: str | None = None,
    has_disability: bool = False,
    disability_details: str | None = None,
    # C - Last Seen
    last_seen_location: str | None = None,
    last_seen_date: str | None = None,
    last_seen_time: str | None = None,
    last_seen_wearing: str | None = None,
    accompanied_by: str | None = None,
    suspected_location: str | None = None,
    # D - Additional
    occupation: str | None = None,
    habits: str | None = None,
    languages_known: str | None = None,
    medical_conditions: str | None = None,
    behavioral_notes: str | None = None,
    description: str | None = None,
    # E - Complainant (inline)
    complainant_name: str | None = None,
    complainant_phone: str | None = None,
    complainant_alt_phone: str | None = None,
    complainant_email: str | None = None,
    complainant_address: str | None = None,
    complainant_relation: str | None = None,
    # Relations
    reported_by: int | None = None,
    created_by: int = 0,
    images: list[UploadFile] | None = None,
) -> MissingPerson:
    """Create a new missing person record with full FIR-level fields."""

    # Create the person first (temporary, no images yet)
    person = MissingPerson(
        name=name, nickname=nickname, age=age, gender=gender,
        date_of_birth=date_of_birth, height=height, weight=weight,
        complexion=complexion, blood_group=blood_group, nationality=nationality,
        identification_marks=identification_marks, face_shape=face_shape,
        hair_color=hair_color, eye_color=eye_color, beard_mustache=beard_mustache,
        has_disability=has_disability, disability_details=disability_details,
        last_seen_location=last_seen_location, last_seen_date=last_seen_date,
        last_seen_time=last_seen_time, last_seen_wearing=last_seen_wearing,
        accompanied_by=accompanied_by, suspected_location=suspected_location,
        occupation=occupation, habits=habits, languages_known=languages_known,
        medical_conditions=medical_conditions, behavioral_notes=behavioral_notes,
        description=description,
        status="missing",
        created_by=created_by,
        reported_by=reported_by,
    )

    # Inline complainant creation
    if complainant_name and complainant_phone and not reported_by:
        comp = Complainant(
            name=complainant_name,
            phone_number=complainant_phone,
            alternate_phone=complainant_alt_phone,
            email=complainant_email,
            address=complainant_address,
            relation_to_person=complainant_relation or "Unknown",
        )
        db.add(comp)
        db.flush()  # get comp.id
        person.reported_by = comp.id

    db.add(person)
    db.flush()  # get person.id

    # Save images into per-person folder
    if images:
        image_paths = _save_images_for_person(person.id, images)
        if image_paths:
            person.image_path = ",".join(image_paths)
            emb_path = _build_embedding(image_paths, person.id, name)
            if emb_path:
                person.embedding_path = emb_path

    db.commit()
    db.refresh(person)
    return person


def get_all_persons(db: Session, status_filter: str | None = None) -> list[MissingPerson]:
    query = db.query(MissingPerson)
    if status_filter:
        query = query.filter(MissingPerson.status == status_filter)
    return query.order_by(MissingPerson.created_at.desc()).all()


def get_person_by_id(db: Session, person_id: int) -> MissingPerson | None:
    return db.query(MissingPerson).filter(MissingPerson.id == person_id).first()


def update_person(db: Session, person_id: int, **kwargs) -> MissingPerson | None:
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
    person = db.query(MissingPerson).filter(MissingPerson.id == person_id).first()
    if not person:
        return False
    # Clean up image folder
    person_dir = IMAGES_DIR / str(person_id)
    if person_dir.exists():
        shutil.rmtree(person_dir, ignore_errors=True)
    db.delete(person)
    db.commit()
    return True
