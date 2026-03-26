import cv2
import threading
import time
import streamlit as st
from eye_tracker import EyeTracker
from strain_monitor import StrainMonitor
from notifier import Notifier
from brightness_control import adjust_brightness

# Initialize objects
eye_tracker = EyeTracker()
strain_monitor = StrainMonitor()
notifier = Notifier()

# Initialize Streamlit session state
if "blinks" not in st.session_state:
    st.session_state.blinks = 0
if "strain_level" not in st.session_state:
    st.session_state.strain_level = "Low"

# Function to run webcam processing
def run_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        blink_detected, total_blinks = eye_tracker.detect_blink(frame)
        strain_monitor.update(total_blinks)
        strain_level = strain_monitor.get_strain_level()

        adjust_brightness(strain_level)

        if strain_level == "High":
            notifier.send_notification("Eye Strain Alert", "High strain detected! Take a break.")

        notifier.check_20_20_20()

        # Update Streamlit session state
        st.session_state.blinks = total_blinks
        st.session_state.strain_level = strain_level

        # Optional: show frame in OpenCV window
        cv2.putText(frame, f"Blink: {total_blinks}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, f"Strain: {strain_level}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        cv2.imshow("Eye Strain Tracker", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# Run webcam in a separate thread
threading.Thread(target=run_webcam, daemon=True).start()

# Streamlit dashboard
st.title("💻 Adaptive Eye Strain Dashboard")
st.metric("Total Blinks", st.session_state.blinks)
st.metric("Current Strain Level", st.session_state.strain_level)