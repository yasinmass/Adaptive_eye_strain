"""
api.py
------
Lightweight Flask API bridge between the browser web app and the
screen brightness controller.

The browser JS POSTs the detected strain level here, and Python
adjusts the physical screen brightness via screen-brightness-control.

Endpoints
---------
POST /strain        { "strain_level": "Low" | "Medium" | "High" }
GET  /brightness    → { "supported": bool, "current_brightness": int }
GET  /health        → { "status": "ok" }

Run
---
  python api.py

Then open the web app at http://localhost:8000
"""

import logging
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

from brightness_control import (
    adjust_brightness,
    get_brightness_status,
    shutdown as brightness_shutdown,
)

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
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)   # Allow requests from http://localhost:8000

VALID_STRAIN_LEVELS = {"Low", "Medium", "High"}


@app.route("/health", methods=["GET"])
def health():
    """Simple liveness check."""
    return jsonify({"status": "ok"})


@app.route("/strain", methods=["POST"])
def set_strain():
    """
    Receive strain level from the browser and trigger brightness adjustment.

    Body (JSON)
    -----------
    { "strain_level": "Low" | "Medium" | "High" }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    strain_level = data.get("strain_level", "").strip().capitalize()

    if strain_level not in VALID_STRAIN_LEVELS:
        return jsonify({
            "error": f"Invalid strain_level '{strain_level}'. "
                     f"Must be one of: {sorted(VALID_STRAIN_LEVELS)}"
        }), 400

    adjust_brightness(strain_level)
    logger.info("Strain level received from browser: %s", strain_level)

    return jsonify({
        "status": "ok",
        "strain_level": strain_level,
        **get_brightness_status(),
    })


@app.route("/brightness", methods=["GET"])
def get_brightness():
    """Return current brightness state for the browser dashboard."""
    return jsonify(get_brightness_status())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Eye Strain Brightness API on http://localhost:5000")
    logger.info("Make sure the web app is served on http://localhost:8000")

    try:
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down API server.")
    finally:
        brightness_shutdown()
        sys.exit(0)
