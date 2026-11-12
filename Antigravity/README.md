# 🐾 Face Filter Camera App (Dog & Cat Filters)

A real-time face filter app with interactive **Dog** and **Cat** filters using your camera.

---

## ✨ Features
* 🐶 **Dog Filter**: Cute floppy ears + dog snout & pink tongue (responds dynamically to mouth opening).
* 🐱 **Cat Filter**: Pointy white/pink cat ears + cute button nose & long whiskers.
* 📸 **Instant Snapshot**: Snap photos with a single keystroke or button click.
* ⚡ **Two Ways to Run**:
  1. **Python (OpenCV)**: Desktop native app with jitter smoothing.
  2. **Browser (WebRTC + MediaPipe)**: Zero-install web version with 3D landmark rotation.

---

## Option 1: Run with Python (Desktop App)

### 1. Install dependencies
In Command Prompt (`cmd`):
```cmd
pip install -r requirements.txt
```
*(Or `pip install opencv-python numpy`)*

### 2. Launch the app
```cmd
python app.py
```
*(Or simply double-click `run.bat`)*

### 🎮 Keyboard Controls:
* <kbd>1</kbd> : Switch to **Dog Filter**
* <kbd>2</kbd> : Switch to **Cat Filter**
* <kbd>0</kbd> : Remove filter
* <kbd>S</kbd> : **Snap photo** (saved into `snapshots/` folder)
* <kbd>Q</kbd> or <kbd>Esc</kbd> : Quit camera

---

## Option 2: Run in your Web Browser (Instant, No Install)

You can run the web version directly in Google Chrome, Microsoft Edge, or Firefox:
1. Double-click the file [web/index.html](file:///c:/Users/ngali/OneDrive/Antigravity/web/index.html).
2. Allow camera access when prompted.
3. Enjoy 60 FPS face tracking with head-tilt rotation and animated tongue!
