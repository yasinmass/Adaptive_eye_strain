import cv2
import mediapipe as mp
import numpy as np
import time

class EyeTracker:
    def __init__(self):
        # Initialize MediaPipe FaceMesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,  # Optimized performance
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.blink_count = 0
        self.eye_closed_frames = 0
        self.state = "CALIBRATING"
        
        self.EAR_THRESHOLD = 0.20 # Default, updated after 10s calibration
        self.CONSEC_FRAMES = 3    # Avoid false positives using 3 consecutive frames
        
        self.calib_start_time = None
        self.calib_ear_values = []
        self.is_calibrated = False

        self.last_blink_detected = False
        self.running = True
        
        # Stored previous EAR for smoothing
        self.prev_ear = None

    def calculate_ear(self, eye):
        """Compute the Eye Aspect Ratio (EAR)"""
        # Distance between vertical eye landmarks
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        # Distance between horizontal eye landmarks
        C = np.linalg.norm(eye[0] - eye[3])
        
        # Prevent Division Error
        if C == 0.0:
            return 0.0
            
        # EAR approximation
        ear = (A + B) / (2.0 * C)
        return ear

    def process_frame(self, frame):
        """Processes a single frame for EAR calculation and blink detection"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        ear = None
        self.last_blink_detected = False

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            h, w, _ = frame.shape

            # Extract MediaPipe eye landmarks
            left_eye_idx = [33, 160, 158, 133, 153, 144]
            right_eye_idx = [362, 385, 387, 263, 373, 380]

            left_eye = np.array([[face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h] for i in left_eye_idx])
            right_eye = np.array([[face_landmarks.landmark[i].x * w, face_landmarks.landmark[i].y * h] for i in right_eye_idx])

            # Calculate individual and average EAR
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            raw_ear = (left_ear + right_ear) / 2.0
            
            # EAR Smoothing (Reduce Noise)
            if self.prev_ear is None:
                self.prev_ear = raw_ear
                
            smooth_ear = 0.7 * self.prev_ear + 0.3 * raw_ear
            self.prev_ear = smooth_ear
            ear = smooth_ear

        if ear is not None:
            if not self.is_calibrated:
                # Calibration Phase
                if self.calib_start_time is None:
                    self.calib_start_time = time.time()
                
                elapsed = time.time() - self.calib_start_time
                
                # Calibration Improvement: Only collect EAR values when EAR > 0.22
                if ear > 0.22:
                    self.calib_ear_values.append(ear)
                
                cv2.putText(frame, f"Calibrating: {max(0, 10 - int(elapsed))}s", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                cv2.putText(frame, "Keep eyes open natively", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                
                if elapsed >= 10:
                    # Fallback if no valid EAR collected
                    if len(self.calib_ear_values) > 0:
                        avg_ear = np.mean(self.calib_ear_values)
                        self.EAR_THRESHOLD = avg_ear * 0.75
                    else:
                        self.EAR_THRESHOLD = 0.25
                        
                    self.is_calibrated = True
                    self.state = "TRACKING"
            else:
                # Tracking Phase
                # Improved blink detection leveraging consecutive frames
                if ear < self.EAR_THRESHOLD:
                    self.eye_closed_frames += 1
                else:
                    if self.eye_closed_frames >= self.CONSEC_FRAMES:
                        self.blink_count += 1
                        self.last_blink_detected = True
                    self.eye_closed_frames = 0
                    
                cv2.putText(frame, f"Blinks: {self.blink_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"EAR: {ear:.2f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.putText(frame, f"Threshold: {self.EAR_THRESHOLD:.2f}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        return frame