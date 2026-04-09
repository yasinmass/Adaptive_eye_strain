"""
app.py
------
Standalone Python backend for the Adaptive Eye Strain Protection System.

Runs headlessly (no GUI window, no Streamlit):
  - Captures webcam frames
  - Runs EAR blink detection via MediaPipe
  - Classifies strain level
  - Adjusts screen brightness smoothly
  - Sends desktop notifications

The web dashboard (web_app/) is served separately via:
  python -m http.server 8000

Press Ctrl+C to quit.
"""

import logging
import threading
import time

import cv2

from brightness_control import adjust_brightness, get_brightness_status, shutdown as brightness_shutdown
from dashboard import start_console_dashboard
from eye_tracker import EyeTracker
from notifier import Notifier
from strain_monitor import StrainMonitor

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TARGET_FPS: int = 15
FRAME_INTERVAL: float = 1.0 / TARGET_FPS


def main() -> None:
    logger.info("Starting Adaptive Eye Strain backend (headless mode).")
    logger.info("Open your browser at http://localhost:8000 for the dashboard.")

    tracker = EyeTracker()
    monitor = StrainMonitor()
    notifier = Notifier()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error(
            "Cannot open webcam (index 0). "
            "Ensure a camera is connected and not in use by another application."
        )
        return

    logger.info("Camera opened. Press Ctrl+C to quit.")

    # ---- Start console dashboard in a daemon thread ----------------------
    dash_thread = threading.Thread(
        target=start_console_dashboard,
        args=(tracker, monitor, get_brightness_status),
        name="ConsoleDashboard",
        daemon=True,
    )
    dash_thread.start()

    last_strain_level: str | None = None

    try:
        while tracker.running:
            tick_start = time.time()

            ret, frame = cap.read()
            if not ret:
                logger.warning("Frame read failed — skipping.")
                time.sleep(0.05)
                continue

            # ---- Eye tracking -----------------------------------------------
            frame = tracker.process_frame(frame)

            if tracker.state == "TRACKING":
                strain_level = monitor.update(
                    blink_detected=tracker.last_blink_detected,
                    eye_closed_frames=tracker.eye_closed_frames,
                )

                # Only push to hardware when strain level actually changes
                if strain_level != last_strain_level:
                    adjust_brightness(strain_level)
                    last_strain_level = strain_level

                    brightness = get_brightness_status()
                    logger.info(
                        "Strain → %-6s | Blink rate: %3d bpm | "
                        "Screen time: %.1f min | Brightness: %s%%",
                        strain_level,
                        monitor.blink_rate,
                        monitor.screen_time,
                        brightness.get("current_brightness", "--")
                        if brightness.get("supported")
                        else "N/A",
                    )

                # Notifications (each has internal cooldown)
                notifier.check_high_strain(strain_level)
                notifier.check_20_20_20()

            else:
                # Reset monitor during calibration so screen-time is accurate
                monitor.start_time = time.time()

            # ---- FPS cap ----------------------------------------------------
            elapsed = time.time() - tick_start
            sleep_for = FRAME_INTERVAL - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    except KeyboardInterrupt:
        logger.info("Ctrl+C received — shutting down gracefully.")

    finally:
        tracker.running = False
        cap.release()
        brightness_shutdown()
        logger.info("Resources released. Goodbye.")


if __name__ == "__main__":
    main()