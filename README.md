# 👁️ Adaptive Eye Strain Protection System

A real-time eye strain detection system that tracks blink patterns, estimates fatigue levels, and automatically adjusts screen brightness — available in both a **browser-based (Web)** version and a **headless Python backend** with hardware brightness control.

---

## 🚀 Features

* 👁️ Blink detection using Eye Aspect Ratio (EAR)
* ⏱️ 10-second personalized calibration
* 📊 Real-time strain monitoring (Low / Medium / High)
* 📉 Live blink-rate graph (Chart.js)
* 💡 Automatic screen brightness adjustment via Python backend
* 🌐 Browser-based dashboard (no install required for web version)
* 🔔 Desktop notifications for high strain events

---

## 🧱 Tech Stack

### 🌐 Web Dashboard (`web_app/`)

* HTML5 / CSS3 / JavaScript
* MediaPipe FaceMesh (JS CDN)
* Chart.js

### 🖥 Python Backend (root)

* Python 3.10+
* Flask + flask-cors
* OpenCV
* MediaPipe
* screen-brightness-control

---

## 📂 Project Structure

```
adaptive_eye_strain/
│
├── web_app/              # 🌐 Deployable frontend (Vercel / static)
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── api.py                # 🔌 Flask API bridge (brightness control)
├── app.py                # 🖥 Headless Python backend (webcam mode)
├── eye_tracker.py        # MediaPipe EAR blink detection
├── strain_monitor.py     # Strain classification logic
├── brightness_control.py # Hardware brightness controller (threaded)
├── dashboard.py          # Console dashboard (used by app.py)
├── notifier.py           # Desktop notification system
└── requirements.txt
```

---

## 🌐 Live Demo

```
https://adaptive-eye-strain.vercel.app
```

---

## ▶️ Running the Project (Local)

The system uses **two concurrent servers**. Both must run at the same time for brightness control to work.

### 1. Clone the Repository

```bash
git clone https://github.com/yasinmass/Adaptive_eye_strain.git
cd Adaptive_eye_strain
```

### 2. Create & Activate Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run — Terminal 1: Flask Brightness API (port 5000)

```bash
python api.py
```

> This starts the Flask server that receives strain level from the browser and adjusts your screen brightness.

### 5. Run — Terminal 2: Web Dashboard (port 8000)

```bash
cd web_app
python -m http.server 8000
```

### 6. Open the Dashboard

```
http://localhost:8000
```

> The browser dashboard will automatically POST the detected strain level to `http://localhost:5000/strain`. No extra steps needed.

---

## 🖥 Headless Python Mode (Webcam Backend)

If you prefer a fully Python-based workflow (no browser required):

```bash
python app.py
```

This runs eye tracking via OpenCV + MediaPipe directly and adjusts brightness without needing the web dashboard.

---

## ⚙️ How It Works

1. Camera captures face in real time (browser or Python)
2. MediaPipe FaceMesh detects eye landmarks
3. EAR (Eye Aspect Ratio) is computed per frame
4. Blinks are detected using dual-threshold hysteresis
5. Strain level is classified every second based on:
   * Blink rate (bpm)
   * Eye closure duration
   * Total screen time
6. Browser POSTs strain level → Flask API → `brightness_control.py` eases brightness smoothly

---

## 📊 Strain & Brightness Mapping

| Strain Level | Condition                          | Target Brightness |
| ------------ | ---------------------------------- | ----------------- |
| Low          | Normal blink rate (> 15 bpm)       | 80%               |
| Medium       | Reduced blinking (8–15 bpm)        | 60%               |
| High         | Very low blinks / long eye closure | 40%               |

---

## 🚀 Deployment (Web Version)

* Platform: **Vercel**
* Root directory: `web_app/`
* No backend required for the dashboard itself
* Brightness control requires the local `api.py` running on `localhost:5000`

---

## ⚠️ Notes

* Camera access requires **HTTPS** or `localhost`
* Works best in good, consistent lighting
* Brightness hardware control requires `screen-brightness-control` (Windows DDC/CI or built-in panel)

---

## 🔧 Future Improvements

* ML-based blink detection (beyond EAR)
* Mobile optimization
* Persistent session history
* User-configurable EAR thresholds

---

## 👨‍💻 Author

Built as a real-time computer vision + health monitoring system.

---

## ⭐ Contribute

Feel free to fork, improve, and submit PRs.
