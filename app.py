import streamlit as st
import cv2
import threading
import time

from eye_tracker import EyeTracker
from strain_monitor import StrainMonitor
from brightness_control import adjust_brightness
from dashboard import render_dashboard

def main():
    # Initialize trackers if not present
    if "tracker" not in st.session_state:
        st.session_state.tracker = EyeTracker()
        st.session_state.monitor = StrainMonitor()
        
        # Track camera state to fix threading issues
        st.session_state.camera_started = False
        st.session_state.last_strain_level = None

    # Start the background thread only once to prevent Streamlit rerun multi-threads
    if not st.session_state.camera_started:
        st.session_state.camera_started = True
        
        def camera_loop():
            cap = cv2.VideoCapture(0)
            target_fps = 15
            frame_time = 1.0 / target_fps
            
            while st.session_state.tracker.running:
                start_t = time.time()
                
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame = st.session_state.tracker.process_frame(frame)
                
                # Check for updates and brightness adjustments
                if st.session_state.tracker.state == "TRACKING":
                    strain_level = st.session_state.monitor.update(
                        st.session_state.tracker.last_blink_detected,
                        st.session_state.tracker.eye_closed_frames
                    )
                    
                    # Brightness Optimization: Only adjust brightness when strain changes
                    if strain_level != st.session_state.last_strain_level:
                        adjust_brightness(strain_level)
                        st.session_state.last_strain_level = strain_level
                else:
                    st.session_state.monitor.start_time = time.time() # Reset clock during calibration
                
                cv2.imshow("Adaptive Eye Strain Tracker - Camera", frame)
                
                # Safe Thread Shutdown using ESC key
                if cv2.waitKey(1) & 0xFF == 27: 
                    st.session_state.tracker.running = False
                    break
                    
                elapsed = time.time() - start_t
                sleep_time = frame_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Release resources gracefully
            cap.release()
            cv2.destroyAllWindows()
            st.session_state.camera_started = False
            
        # Spawn daemon thread so it guarantees exit when Streamlit terminates
        threading.Thread(target=camera_loop, daemon=True).start()

    # Pass instances to render the live UI
    render_dashboard(st.session_state.tracker, st.session_state.monitor)

if __name__ == "__main__":
    main()