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
from app.pipeline.face_detector import RetinaFaceDetector
from app.pipeline.face_embedder import ArcFaceEmbedder
from app.core.face_matcher import FaceMatcher
from app.models.missing_person import MissingPerson
from app.models.detection_log import DetectionLog

detector = RetinaFaceDetector()
embedder = ArcFaceEmbedder()
matcher = FaceMatcher(threshold=0.50)

def _load_all_embeddings(db: Session, target_person_id: int | None = None) -> list[tuple[int, list[float]]]:
    """Load all stored embeddings for missing persons with status='missing'."""
    query = (
        db.query(MissingPerson)
        .filter(MissingPerson.status == "missing")
        .filter(MissingPerson.embedding_path.isnot(None))
    )
    if target_person_id is not None:
        query = query.filter(MissingPerson.id == target_person_id)
        
    import json
    persons = query.all()
    candidates = []
    for p in persons:
        try:
            with open(p.embedding_path) as f:
                emb = json.load(f)
                candidates.append((p.id, emb))
        except Exception:
            pass
    return candidates


def run_detection_on_video(
    db: Session,
    video_path: str,
    camera_id: int | None = None,
    target_person_id: int | None = None,
) -> list[dict]:
    """
    Process a video file: extract frames, detect faces, compare embeddings.
    Returns a list of match results inserted into detection_logs.
    """
    candidates = _load_all_embeddings(db, target_person_id)
    if not candidates:
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    results = []
    frame_idx = 0
    seen_matches: dict[int, float] = {}  # person_id → best confidence

    print(f"[run_detection] Started processing video. Total candidates: {len(candidates)}")
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print(f"[run_detection] Video ended or cannot read frame at index {frame_idx}")
                break

            frame_idx += 1
            if frame_idx % FRAME_SKIP != 0:
                continue

            print(f"[run_detection] Processing frame {frame_idx}...")
            # Detect faces in this frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            dets = detector.detect_and_align(rgb)
            if not dets:
                continue

            print(f"[run_detection] Found {len(dets)} face(s) in frame {frame_idx}")
            for det in dets:
                if det.aligned_face is None:
                    continue

                # Encode face
                probe = embedder.embed(det.aligned_face)
                if probe is None:
                    continue

                # Match against all missing persons
                best = matcher.find_best(probe.tolist(), candidates)
                if best is None:
                    continue

                person_id, similarity = best
                confidence = round(similarity * 100, 2)
                # Compute approximate timestamp
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                timestamp_sec = frame_idx / fps

                # Cooldown: Log the same person at most once every 5 seconds of video time
                if person_id in seen_matches:
                    last_time = seen_matches[person_id]
                    if (timestamp_sec - last_time) < 5.0:
                        continue
                
                seen_matches[person_id] = timestamp_sec

                # Save snapshot with bounding box
                x, y, w, h = det.bbox
                annotated = frame.copy()
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 100), 2)
                label = f"Match {confidence}%"
                cv2.putText(annotated, label, (x, max(0, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 100), 2)
                
                snap_name = f"match_{person_id}_{uuid.uuid4().hex[:8]}.jpg"
                snap_path = str(OUTPUTS_DIR / snap_name)
                web_path = f"data/outputs/{snap_name}"
                cv2.imwrite(snap_path, annotated)

                # Compute approximate timestamp
                ts = datetime.now(timezone.utc)

                # Insert detection log
                log = DetectionLog(
                    person_id=person_id,
                    camera_id=camera_id,
                    timestamp=ts,
                    confidence_score=confidence,
                    image_snapshot_path=web_path,
                    video_time_sec=round(timestamp_sec, 2),
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
            "video_time_sec": log.video_time_sec,
            "confidence_score": log.confidence_score,
            "status": getattr(log, 'status', 'pending') or 'pending',
            "snapshot_path": log.image_snapshot_path,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return results
