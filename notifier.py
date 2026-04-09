"""
notifier.py
-----------
Handles desktop notifications and 20-20-20 eye-break reminders.

Features:
  - Cooldown guard so High-strain alerts are not spammed
  - Graceful fallback when plyer is unavailable
  - Structured logging
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from plyer import notification as _plyer_notify
    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False
    logger.warning(
        "plyer is not installed; desktop notifications are disabled. "
        "Install with: pip install plyer"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REMINDER_INTERVAL_SECONDS: int = 20 * 60        # 20-minute 20-20-20 rule
HIGH_STRAIN_COOLDOWN_SECONDS: int = 5 * 60      # Suppress repeated High-strain alerts


class Notifier:
    """
    Send system-level desktop notifications.

    Attributes
    ----------
    last_20_20_20_time : float
        Epoch time when the last 20-20-20 reminder was fired.
    _last_high_strain_time : float
        Epoch time of the last High-strain notification (for cooldown).
    """

    def __init__(self) -> None:
        self.last_20_20_20_time: float = time.time()
        self._last_high_strain_time: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_notification(self, title: str, message: str, timeout: int = 5) -> None:
        """
        Display a desktop notification.

        Parameters
        ----------
        title   : Notification title.
        message : Notification body.
        timeout : Seconds the notification stays visible (plyer default = 5).
        """
        logger.info("Notification → [%s] %s", title, message)

        if not _PLYER_AVAILABLE:
            # Soft fallback: print to console so the user still sees alerts
            print(f"[NOTIFICATION] {title}: {message}")
            return

        try:
            _plyer_notify.notify(
                title=title,
                message=message,
                app_name="Adaptive Eye Strain",
                timeout=timeout,
            )
        except Exception as exc:
            logger.warning("Could not send notification: %s", exc)

    def check_high_strain(self, strain_level: str) -> None:
        """
        Send a High-strain alert with cooldown to prevent alert fatigue.

        Parameters
        ----------
        strain_level : str
            Current strain level ("Low", "Medium", or "High").
        """
        if strain_level != "High":
            return

        now = time.time()
        if now - self._last_high_strain_time >= HIGH_STRAIN_COOLDOWN_SECONDS:
            self.send_notification(
                "⚠️ Eye Strain Alert",
                "High strain detected! Take a short break and rest your eyes.",
            )
            self._last_high_strain_time = now

    def check_20_20_20(self) -> None:
        """
        Fire the 20-20-20 reminder every REMINDER_INTERVAL_SECONDS.
        """
        now = time.time()
        if now - self.last_20_20_20_time >= REMINDER_INTERVAL_SECONDS:
            self.send_notification(
                "👁️ 20-20-20 Break",
                "Look at something 20 feet away for 20 seconds to reduce strain!",
                timeout=8,
            )
            self.last_20_20_20_time = now
            logger.info("20-20-20 reminder fired.")