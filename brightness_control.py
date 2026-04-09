"""
brightness_control.py
---------------------
Manages automatic screen brightness based on eye-strain level.

Features:
  - Smooth exponential easing transitions (no sudden jumps)
  - Per-monitor support via screen_brightness_control
  - Graceful fallback when hardware control is unavailable
  - Thread-safe design with a single daemon worker
  - Redundant-write prevention (WRITE_THRESHOLD + last-written cache)
  - Clean shutdown with thread join
  - Structured logging without spam
  - Full encapsulation (no private attr access from outside)
"""

import threading
import time
import logging
from typing import Optional

# screen_brightness_control may not be available on every platform/monitor.
# We import it lazily so the rest of the system still works if it is absent.
try:
    import screen_brightness_control as sbc
    _SBC_AVAILABLE = True
except ImportError:
    _SBC_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Target brightness (0–100) for each strain level
BRIGHTNESS_TARGETS: dict[str, int] = {
    "Low":    80,
    "Medium": 60,
    "High":   40,
}

# Valid brightness range (inclusive)
BRIGHTNESS_MIN: int = 0
BRIGHTNESS_MAX: int = 100

# How many easing steps are attempted per second
TRANSITION_STEPS_PER_SECOND: int = 25          # slightly higher → more responsive

# Exponential ease-factor per tick; keep in (0, 1).
# Larger → faster convergence.
EASE_FACTOR: float = 0.15                       # was 0.12 — snappier without jarring

# Minimum brightness delta (floating-point) before we write to hardware
WRITE_THRESHOLD: float = 0.75                   # was 1.0 — catches near-final steps sooner

# Delta below which we snap directly to target (avoids infinite asymptote)
SNAP_THRESHOLD: float = 0.3

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BrightnessController
# ---------------------------------------------------------------------------

class BrightnessController:
    """
    Thread-safe brightness manager with smooth easing transitions.

    Usage
    -----
    controller = BrightnessController()
    controller.set_strain_level("High")   # call from any thread
    controller.stop()                     # clean shutdown
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()      # cleaner than a plain bool flag

        self._supported: bool = False
        self._current: float = 80.0
        self._target: float = 80.0
        self._last_written: int = -1              # last value actually sent to HW
        self._last_write_error: str = ""          # dedup consecutive identical errors
        self._monitor_names: list[str] = []

        self._probe_hardware()

        # Daemon thread — exits automatically when the main program exits
        self._thread = threading.Thread(
            target=self._transition_loop,
            name="BrightnessTransitionThread",
            daemon=True,
        )
        self._thread.start()

        logger.info(
            "BrightnessController started | hardware_supported=%s | initial=%d%%",
            self._supported,
            int(self._current),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_strain_level(self, strain_level: str) -> None:
        """
        Queue a smooth brightness transition for the given strain level.

        Parameters
        ----------
        strain_level : str
            One of "Low", "Medium", "High".
        """
        target = BRIGHTNESS_TARGETS.get(strain_level)
        if target is None:
            logger.warning(
                "Unknown strain level '%s'. Expected one of %s.",
                strain_level,
                list(BRIGHTNESS_TARGETS.keys()),
            )
            return

        # Clamp just in case the constant table ever has out-of-range values
        clamped = _clamp(float(target))
        with self._lock:
            self._target = clamped

        logger.debug(
            "Strain level → '%s' | target brightness %d%%", strain_level, int(clamped)
        )

    def set_brightness_direct(self, value: int) -> None:
        """
        Immediately set both target and current to *value* (0–100), bypassing easing.
        Useful for manual overrides or initial calibration.
        """
        clamped = _clamp(float(value))
        with self._lock:
            self._target = clamped
            self._current = clamped
        self._write_brightness(int(round(clamped)))

    @property
    def current_brightness(self) -> int:
        """Interpolated current brightness (may differ from HW value mid-transition)."""
        with self._lock:
            return int(round(self._current))

    @property
    def target_brightness(self) -> int:
        """The brightness value we are currently easing toward."""
        with self._lock:
            return int(round(self._target))

    @property
    def is_supported(self) -> bool:
        """True when hardware brightness control is available."""
        return self._supported

    @property
    def monitor_names(self) -> list[str]:
        """Names of detected monitors (may be empty for generic/unnamed monitors)."""
        return list(self._monitor_names)

    def stop(self, timeout: float = 2.0) -> None:
        """
        Signal the background thread to exit and wait for it to finish.

        Parameters
        ----------
        timeout : float
            Maximum seconds to wait for the thread to join (default 2 s).
        """
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            logger.warning("BrightnessTransitionThread did not stop within %.1f s.", timeout)
        else:
            logger.info("BrightnessController stopped cleanly.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _probe_hardware(self) -> None:
        """
        Detect whether screen_brightness_control can reach the hardware.
        Populates self._supported, self._current, self._target, and
        self._monitor_names.
        """
        if not _SBC_AVAILABLE:
            logger.warning(
                "screen_brightness_control is not installed. "
                "Brightness control is disabled. "
                "Install it with:  pip install screen-brightness-control"
            )
            return

        try:
            monitors = sbc.list_monitors()
            self._monitor_names = list(monitors) if monitors else []

            raw = sbc.get_brightness()

            # sbc may return a list (one entry per monitor) or a bare int
            if isinstance(raw, (list, tuple)):
                value = raw[0] if raw else None
            else:
                value = raw

            if value is None:
                raise ValueError("get_brightness() returned None — monitor may not support DDC/CI")

            clamped = _clamp(float(value))
            self._current = clamped
            self._target = clamped
            self._last_written = int(round(clamped))
            self._supported = True

            logger.info(
                "Monitors detected: %d (%s) | Current brightness: %d%%",
                len(self._monitor_names),
                self._monitor_names or ["(unnamed)"],
                int(clamped),
            )

        except Exception as exc:
            logger.warning(
                "Hardware brightness control unavailable: %s. "
                "System will run without screen dimming.",
                exc,
            )
            self._supported = False

    def _write_brightness(self, value: int) -> None:
        """
        Send a clamped brightness integer to all detected monitors.

        Guards:
        - Skips if hardware is unsupported.
        - Skips if the value is identical to the last written value.
        - Logs repeated identical errors only once (dedup).
        """
        if not self._supported:
            return

        value = int(_clamp(float(value)))           # always safe

        with self._lock:
            if value == self._last_written:
                return
            # Optimistically mark as written; revert on failure below
            self._last_written = value

        try:
            if self._monitor_names:
                for monitor in self._monitor_names:
                    sbc.set_brightness(value, display=monitor)
            else:
                sbc.set_brightness(value)

            self._last_write_error = ""             # clear dedup buffer on success
            logger.debug("HW brightness → %d%%", value)

        except Exception as exc:
            err_msg = str(exc)
            # Revert the optimistic write so we retry next tick
            with self._lock:
                self._last_written = -1
            # Only log if the message changed (avoids flooding the log)
            if err_msg != self._last_write_error:
                logger.warning("Failed to set hardware brightness: %s", exc)
                self._last_write_error = err_msg

    def _transition_loop(self) -> None:
        """
        Background loop: exponentially ease self._current toward self._target
        and write to hardware whenever the value changes meaningfully.
        """
        interval = 1.0 / TRANSITION_STEPS_PER_SECOND

        while not self._stop_event.wait(timeout=interval):
            with self._lock:
                target = self._target
                current = self._current

            delta = target - current

            if abs(delta) <= SNAP_THRESHOLD:
                # Snap to target to avoid the infinite asymptote
                if abs(delta) > 0:
                    with self._lock:
                        self._current = target
                    self._write_brightness(int(round(target)))
            elif abs(delta) > WRITE_THRESHOLD:
                # Exponential ease step
                current += delta * EASE_FACTOR
                current = _clamp(current)

                with self._lock:
                    self._current = current

                self._write_brightness(int(round(current)))


# ---------------------------------------------------------------------------
# Brightness clamp helper
# ---------------------------------------------------------------------------

def _clamp(value: float) -> float:
    """Return *value* clamped to [BRIGHTNESS_MIN, BRIGHTNESS_MAX]."""
    return max(float(BRIGHTNESS_MIN), min(float(BRIGHTNESS_MAX), value))


# ---------------------------------------------------------------------------
# Module-level singleton and public convenience functions
# ---------------------------------------------------------------------------

_controller: Optional[BrightnessController] = None
_controller_lock = threading.Lock()


def _get_controller() -> BrightnessController:
    """Return the shared BrightnessController, creating it lazily on first call."""
    global _controller
    with _controller_lock:
        if _controller is None:
            _controller = BrightnessController()
    return _controller


def adjust_brightness(strain_level: str) -> None:
    """
    Public entry-point used by app.py / main.py.

    Smoothly adjusts screen brightness based on the detected eye-strain level.

    Parameters
    ----------
    strain_level : str
        One of "Low", "Medium", or "High".
    """
    _get_controller().set_strain_level(strain_level)


def get_brightness_status() -> dict:
    """
    Return a snapshot of the current brightness state for dashboard display.

    Returns
    -------
    dict
        supported        (bool)  – whether HW control is available
        current_brightness (int) – interpolated current level (0–100)
        target_brightness  (int) – level we are easing toward (0–100)
        monitors         (list)  – names of detected monitors
    """
    ctrl = _get_controller()
    return {
        "supported":          ctrl.is_supported,
        "current_brightness": ctrl.current_brightness,   # public property
        "target_brightness":  ctrl.target_brightness,    # public property — no _attr access
        "monitors":           ctrl.monitor_names,
    }


def shutdown() -> None:
    """
    Clean up the brightness controller on application exit.

    Blocks briefly to allow the background thread to finish gracefully.
    """
    global _controller
    with _controller_lock:
        if _controller is not None:
            _controller.stop()
            _controller = None