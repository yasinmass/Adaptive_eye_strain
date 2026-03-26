import cv2
import mediapipe as mp
import time

class EyeTracker:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.blink_counter = 0
        self.eye_aspect_ratio_threshold = 0.25
        self.prev_blink_time = time.time()
    
    def calculate_ear(self, landmarks, eye_indices):
        # EAR calculation for blink detection
        # landmarks: list of (x, y)
        p1 = landmarks[eye_indices[0]]
        p2 = landmarks[eye_indices[1]]
        p3 = landmarks[eye_indices[2]]
        p4 = landmarks[eye_indices[3]]
        p5 = landmarks[eye_indices[4]]
        p6 = landmarks[eye_indices[5]]
        # Vertical distance / horizontal distance
        vertical = ((p2[1]-p6[1]) + (p3[1]-p5[1])) / 2
        horizontal = p1[0] - p4[0]
        ear = vertical / horizontal
        return ear
    
    def detect_blink(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        blink_detected = False

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            h, w, _ = frame.shape
            points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

            left_eye_indices = [33, 159, 158, 133, 153, 144]
            right_eye_indices = [362, 386, 387, 263, 373, 380]

            left_ear = self.calculate_ear(points, left_eye_indices)
            right_ear = self.calculate_ear(points, right_eye_indices)

            ear = (left_ear + right_ear) / 2

            if ear < self.eye_aspect_ratio_threshold:
                if time.time() - self.prev_blink_time > 0.2:  # debounce
                    self.blink_counter += 1
                    self.prev_blink_time = time.time()
                    blink_detected = True
        return blink_detected, self.blink_counter