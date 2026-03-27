# 👁️ Adaptive Eye Strain Protection System

A real-time eye strain detection system that tracks blink patterns, estimates fatigue levels, and provides visual feedback — available in both **desktop (Python)** and **browser-based (Web)** versions.

---

## 🚀 Features

* 👁️ Blink detection using Eye Aspect Ratio (EAR)
* ⏱️ 10-second personalized calibration
* 📊 Real-time strain monitoring (Low / Medium / High)
* 📉 Live graph (blink rate & strain trend)
* 💡 Automatic brightness adjustment (Python version)
* 🌐 Browser-based version (no installation required)

---

## 🧱 Tech Stack

### 🖥 Python Version (Local App)

* Python 3.10+
* OpenCV
* MediaPipe
* NumPy
* Streamlit
* screen-brightness-control

### 🌐 Web Version (Deployed)

* HTML5
* CSS3
* JavaScript
* MediaPipe JS (FaceMesh)
* Chart.js

---

## 📂 Project Structure

```
adaptive_eye_strain/
│
├── web_app/              # 🌐 Deployable frontend (Vercel)
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── README.md
│
├── python_app/           # 🖥 Local CV application
│   ├── app.py
│   ├── eye_tracker.py
│   ├── strain_monitor.py
│   ├── brightness_control.py
│   ├── dashboard.py
│   ├── notifier.py
│   └── requirements.txt
```

---

## 🌐 Live Demo

After deployment (Vercel):

```
https://your-project.vercel.app
```

---

## 🧪 Run Web Version (Local)

```
cd web_app
python -m http.server 8000
```

Open:

```
http://localhost:8000
```

---

## 🖥 Run Python Version (Local)

### 1. Clone Repository

```
git clone https://github.com/<your-username>/adaptive_eye_strain.git
cd adaptive_eye_strain/python_app
```

---

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## ⚠️ Windows Setup (Important for dlib / build tools)

> Only required if you extend project with dlib or advanced builds

### Install CMake

* Download: https://cmake.org/download/
* Install and **enable "Add to PATH"**

---

### Install Visual Studio Build Tools

* Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
* Install:

  * ✔ Desktop development with C++

---

## ▶️ Run Application

```
streamlit run app.py
```

---

## ⚙️ How It Works

1. Camera captures face in real time
2. MediaPipe detects eye landmarks
3. EAR (Eye Aspect Ratio) is computed
4. Blinks are detected using threshold + frame validation
5. Strain level is estimated based on:

   * Blink rate
   * Eye closure duration
   * Screen time
6. Output is displayed in UI + dashboard

---

## 📊 Strain Logic

| Condition                        | Result |
| -------------------------------- | ------ |
| Normal blink rate                | Low    |
| Reduced blinking                 | Medium |
| Very low blinking / long closure | High   |

---

## 🚀 Deployment (Web Version)

* Platform: Vercel
* Root Directory: `web_app`
* No backend required
* Uses browser camera + MediaPipe JS

---

## ⚠️ Notes

* Camera requires **HTTPS** (works on Vercel)
* Works best in good lighting
* Accuracy depends on face visibility and camera angle

---

## 🔧 Future Improvements

* Better blink detection (ML-based)
* Mobile optimization
* Notification system in web version
* User settings (threshold tuning)

---

## 👨‍💻 Author

Built as a real-time CV + health monitoring system for hackathons and productivity tools.

---

## ⭐ Contribute

Feel free to fork, improve, and submit PRs.
