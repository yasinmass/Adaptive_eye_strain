"""
dashboard.py
------------
Console status dashboard for the Adaptive Eye Strain System.

Prints a live-refreshing terminal HUD with:
  - Calibration state
  - Blink count & rate
  - Screen time
  - Strain level (colour-coded via ANSI codes)
  - Screen brightness (if hardware control is available)

Import and call `print_status()` from your main loop, or run directly
for a standalone demo.

No external dependencies beyond the project modules.
"""

import os
import time
import shutil
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ANSI colour codes (work on Windows 10+ terminals and all Unix terminals)
# ---------------------------------------------------------------------------
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_DIM    = "\033[2m"

STRAIN_ANSI: dict[str, str] = {
    "Low":    _GREEN,
    "Medium": _YELLOW,
    "High":   _RED,
}

# How often (seconds) the full HUD is re-drawn
REFRESH_INTERVAL: float = 1.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _term_width() -> int:
    """Return terminal width, defaulting to 60 if detection fails."""
    try:
        return shutil.get_terminal_size(fallback=(60, 24)).columns
    except Exception:
        return 60


def _bar(value: int, max_value: int = 100, width: int = 20) -> str:
    """Render a simple ASCII progress bar."""
    filled = int(round(width * max(0, min(value, max_value)) / max_value))
    return f"[{'█' * filled}{'░' * (width - filled)}] {value:3d}%"


def _clear() -> None:
    """Clear the terminal screen cross-platform."""
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def print_status(
    tracker,
    monitor,
    brightness_info: dict | None = None,
    *,
    clear_screen: bool = True,
) -> None:
    """
    Print a one-shot status snapshot to the terminal.

    Parameters
    ----------
    tracker         : EyeTracker instance
    monitor         : StrainMonitor instance
    brightness_info : dict from brightness_control.get_brightness_status()
    clear_screen    : If True, clears terminal before printing (default).
    """
    if clear_screen:
        _clear()

    width  = _term_width()
    divider = _DIM + "─" * width + _RESET

    strain       = monitor.current_strain
    strain_color = STRAIN_ANSI.get(strain, _RESET)
    state        = tracker.state

    print(divider)
    print(f"{_BOLD}{_CYAN}  👁  Adaptive Eye Strain Monitor{_RESET}")
    print(divider)

    # ---- State -----------------------------------------------------------
    if state == "CALIBRATING":
        print(f"  Status  : {_YELLOW}⚙  CALIBRATING…{_RESET}  (keep eyes open)")
    else:
        print(f"  Status  : {_GREEN}✔  TRACKING ACTIVE{_RESET}")

    print()

    # ---- Metrics --------------------------------------------------------
    print(f"  Blinks      : {_BOLD}{tracker.blink_count}{_RESET}")
    print(f"  Blink rate  : {_BOLD}{monitor.blink_rate} bpm{_RESET}")
    print(f"  Screen time : {_BOLD}{monitor.screen_time:.1f} min{_RESET}")
    print(
        f"  Strain level: "
        f"{_BOLD}{strain_color}{strain}{_RESET}"
    )

    if tracker.prev_ear is not None:
        print(f"  EAR         : {tracker.prev_ear:.4f}  "
              f"(threshold: {tracker.EAR_THRESHOLD:.4f})")

    print()

    # ---- Brightness -----------------------------------------------------
    if brightness_info and brightness_info.get("supported"):
        b = brightness_info.get("current_brightness", 0)
        print(f"  Brightness  : {_bar(b)}")
    else:
        print(f"  Brightness  : {_DIM}hardware control not available{_RESET}")

    print()
    print(divider)
    print(f"  {_DIM}Press Ctrl+C to quit{_RESET}")
    print(divider)


# ---------------------------------------------------------------------------
# Standalone polling loop (optional — call from app.py / main.py instead)
# ---------------------------------------------------------------------------

def start_console_dashboard(
    tracker,
    monitor,
    get_brightness_fn,
    refresh: float = REFRESH_INTERVAL,
) -> None:
    """
    Block and continuously refresh the terminal HUD.

    Parameters
    ----------
    tracker           : EyeTracker instance
    monitor           : StrainMonitor instance
    get_brightness_fn : Callable → dict  (e.g. brightness_control.get_brightness_status)
    refresh           : Seconds between redraws
    """
    logger.info("Console dashboard started (refresh=%.1fs). Press Ctrl+C to stop.", refresh)
    try:
        while tracker.running:
            brightness_info = get_brightness_fn()
            print_status(tracker, monitor, brightness_info)
            time.sleep(refresh)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Console dashboard stopped.")