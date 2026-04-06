from app.database import SessionLocal
from app.services.face_service import run_detection_on_video
import cv2
import numpy as np

def run_test():
    db = SessionLocal()
    # Create a dummy video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('dummy.mp4', fourcc, 20.0, (640,480))
    for _ in range(60):
        # A white square representing a "face" or just noise
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    
    print("Testing run_detection_on_video")
    try:
        results = run_detection_on_video(db, 'dummy.mp4', camera_id=None, target_person_id=None)
        print(f"Finished correctly. Results: {len(results)}")
    except Exception as e:
        print(f"Exception exactly: {e}")

if __name__ == "__main__":
    run_test()
