"""
services/face_service.py
High-level face processing — encoding images, running detection on videos.
"""
from __future__ import annotations
import cv2
import uuid
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import EMBEDDINGS_DIR, OUTPUTS_DIR, FRAME_SKIP
from app.core.face_detector import FaceDetector
from app.core.face_encoder import FaceEncoder
from app.core.face_matcher import FaceMatcher
from app.models.missing_person import MissingPerson
from app.models.detection_log import DetectionLog

detector = FaceDetector()
encoder = FaceEncoder()
matcher = FaceMatcher()


def _load_all_embeddings(db: Session) -> list[tuple[int, list[float]]]:
    """Load all stored embeddings for missing persons with status='missing'."""
    persons = (
        db.query(MissingPerson)
        .filter(MissingPerson.status == "missing")
        .filter(MissingPerson.embedding_path.isnot(None))
        .all()
    )
    candidates = []
    for p in persons:
        emb = encoder.load_embedding(p.embedding_path)
        if emb:
            candidates.append((p.id, emb))
    return candidates


def run_detection_on_video(
    db: Session,
    video_path: str,
    camera_id: int | None = None,
) -> list[dict]:
    """
    Process a video file: extract frames, detect faces, compare embeddings.
    Returns a list of match results inserted into detection_logs.
    """
    candidates = _load_all_embeddings(db)
    if not candidates:
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    results = []
    frame_idx = 0
    seen_matches: dict[int, float] = {}  # person_id → best confidence

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % FRAME_SKIP != 0:
                continue

            # Detect faces in this frame
            boxes = detector.detect_from_frame(frame)
            if not boxes:
                continue

            for (x, y, w, h) in boxes:
                # Crop face region
                face_crop = frame[y:y + h, x:x + w]
                if face_crop.size == 0:
                    continue

                # Encode face
                probe = encoder.encode_frame(face_crop)
                if not probe:
                    continue

                # Match against all missing persons
                best = matcher.find_best(probe, candidates)
                if best is None:
                    continue

                person_id, similarity = best
                confidence = round(similarity * 100, 2)

                # Only keep the best match per person
                if person_id in seen_matches and seen_matches[person_id] >= confidence:
                    continue
                seen_matches[person_id] = confidence

                # Save snapshot with bounding box
                annotated = detector.draw_boxes(frame, [(x, y, w, h)], label=f"Match {confidence}%")
                snap_name = f"match_{person_id}_{uuid.uuid4().hex[:8]}.jpg"
                snap_path = str(OUTPUTS_DIR / snap_name)
                cv2.imwrite(snap_path, annotated)

                # Compute approximate timestamp
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                timestamp_sec = frame_idx / fps
                ts = datetime.now(timezone.utc)

                # Insert detection log
                log = DetectionLog(
                    person_id=person_id,
                    camera_id=camera_id,
                    timestamp=ts,
                    confidence_score=confidence,
                    image_snapshot_path=snap_path,
                )
                db.add(log)

                results.append({
                    "person_id": person_id,
                    "confidence": confidence,
                    "frame": frame_idx,
                    "video_time_sec": round(timestamp_sec, 2),
                    "snapshot_path": snap_path,
                })

        db.commit()
    finally:
        cap.release()

    return results


def get_detection_results(db: Session, person_id: int | None = None) -> list[dict]:
    """Retrieve detection logs, optionally filtered by person_id."""
    query = db.query(DetectionLog)
    if person_id:
        query = query.filter(DetectionLog.person_id == person_id)
    logs = query.order_by(DetectionLog.created_at.desc()).all()

    results = []
    for log in logs:
        person = log.person
        results.append({
            "id": log.id,
            "person_id": log.person_id,
            "person_name": person.name if person else "Unknown",
            "camera_id": log.camera_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "confidence_score": log.confidence_score,
            "snapshot_path": log.image_snapshot_path,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return results
