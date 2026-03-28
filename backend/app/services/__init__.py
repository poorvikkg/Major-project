from app.services.auth_service import authenticate_user
from app.services.person_service import (
    add_person, get_all_persons, get_person_by_id, update_person, delete_person,
)
from app.services.face_service import run_detection_on_video, get_detection_results
from app.services.video_service import save_uploaded_video, generate_live_frames
from app.services.match_service import compare_two_images
from app.services.alert_service import send_detection_alert

__all__ = [
    "authenticate_user",
    "add_person", "get_all_persons", "get_person_by_id", "update_person", "delete_person",
    "run_detection_on_video", "get_detection_results",
    "save_uploaded_video", "generate_live_frames",
    "compare_two_images",
    "send_detection_alert",
]
