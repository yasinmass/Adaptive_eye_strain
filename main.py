"""
main.py
-------
Alternative entry-point that shows a live OpenCV preview window
alongside the brightness control and notifications.

Use this if you want to see the camera feed with EAR/blink overlay.
For headless (no window) operation, run app.py instead.

Press ESC or Ctrl+C to quit.
"""

import logging
import time

import cv2

from brightness_control import adjust_brightness, get_brightness_status, shutdown as brightness_shutdown
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
WINDOW_TITLE: str = "Adaptive Eye Strain Tracker  |  ESC to quit"

# Overlay text colours per strain level (BGR)
STRAIN_COLOURS: dict[str, tuple[int, int, int]] = {
    "Low":    (0, 200, 0),    # green
    "Medium": (0, 165, 255),  # orange
    "High":   (0, 0, 220),    # red
}


def _draw_hud(
    frame,
    tracker: EyeTracker,
    monitor: StrainMonitor,
    brightness_info: dict,
) -> None:
    """Render a minimal heads-up display on the camera frame."""
    strain  = monitor.current_strain
    colour  = STRAIN_COLOURS.get(strain, (255, 255, 255))
    font    = cv2.FONT_HERSHEY_SIMPLEX

    lines = [
        f"Blinks     : {tracker.blink_count}",
        f"Blink rate : {monitor.blink_rate} bpm",
        f"Screen time: {monitor.screen_time:.1f} min",
        f"Strain     : {strain}",
        f"EAR        : {tracker.prev_ear:.3f}" if tracker.prev_ear else "EAR: --",
    ]

    if brightness_info.get("supported"):
        lines.append(f"Brightness : {brightness_info.get('current_brightness', '--')}%")
    else:
        lines.append("Brightness : not supported")

    for i, text in enumerate(lines):
        y = 30 + i * 30
        # Shadow for readability on any background
        cv2.putText(frame, text, (16, y + 1), font, 0.62, (0, 0, 0),    2, cv2.LINE_AA)
        cv2.putText(frame, text, (15, y),     font, 0.62, colour,        1, cv2.LINE_AA)


def main() -> None:
    logger.info("Starting Adaptive Eye Strain Tracker (preview mode).")

    tracker  = EyeTracker()
    monitor  = StrainMonitor()
    notifier = Notifier()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error(
            "Cannot open webcam (index 0). "
            "Ensure a camera is connected and not in use by another application."
        )
        return

    logger.info("Camera opened. Press ESC to quit.")

    last_strain_level: str | None = None
    brightness_info: dict = {}

    try:
        while tracker.running:
            tick_start = time.time()

            ret, frame = cap.read()
            if not ret:
                logger.warning("Frame read failed — retrying.")
                time.sleep(0.05)
                continue

            # ---- Process frame (writes blink/EAR state onto tracker) ------
            frame = tracker.process_frame(frame)

            if tracker.state == "TRACKING":
                strain_level = monitor.update(
                    blink_detected=tracker.last_blink_detected,
                    eye_closed_frames=tracker.eye_closed_frames,
                )

                # Push brightness change only when strain changes
                if strain_level != last_strain_level:
                    adjust_brightness(strain_level)
                    last_strain_level = strain_level
                    logger.info(
                        "Strain → %s | Blink rate: %d bpm | Screen time: %.1f min",
                        strain_level, monitor.blink_rate, monitor.screen_time,
                    )

                brightness_info = get_brightness_status()

                notifier.check_high_strain(strain_level)
                notifier.check_20_20_20()

                _draw_hud(frame, tracker, monitor, brightness_info)

            else:
                # Calibration: keep monitor clock reset
                monitor.start_time = time.time()

            # ---- Display --------------------------------------------------
            cv2.imshow(WINDOW_TITLE, frame)
            if cv2.waitKey(1) & 0xFF == 27:   # ESC
                logger.info("ESC pressed — shutting down.")
                tracker.running = False
                break

            # ---- FPS cap --------------------------------------------------
            elapsed   = time.time() - tick_start
            sleep_for = FRAME_INTERVAL - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    except KeyboardInterrupt:
        logger.info("Ctrl+C received — shutting down gracefully.")

    finally:
        tracker.running = False
        cap.release()
        cv2.destroyAllWindows()
        brightness_shutdown()
        logger.info("Resources released. Goodbye.")


if __name__ == "__main__":
    main()