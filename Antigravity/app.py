"""
Live Face Filter Camera App (Dog & Cat Filters)
Features:
- Real-time face tracking via OpenCV Haar Cascades
- Smooth tracking with Exponential Moving Average (EMA) to prevent jitter
- Dog filter: floppy ears + snout & tongue
- Cat filter: pointy cat ears + whiskers & cute pink nose
- Instant photo snapshot capture (saved to 'snapshots/' folder)
- Live on-screen controls and HUD
"""

import os
import sys
import time
from datetime import datetime

# Helpful import error message if packages are missing
try:
    import cv2
    import numpy as np
except ImportError:
    print("\n" + "=" * 65)
    print("ERROR: Required libraries 'opencv-python' or 'numpy' are missing!")
    print("\nTo install them, open your Command Prompt (CMD) and run:")
    print("    pip install opencv-python numpy")
    print("=" * 65 + "\n")
    input("Press Enter to exit...")
    sys.exit(1)


def overlay_transparent(background, overlay, x, y, width=None, height=None):
    """
    Overlays a transparent RGBA image onto a BGR background image at (x, y)
    with safe bounds clipping for edges of the screen.
    """
    if overlay is None or overlay.size == 0:
        return background

    # Resize overlay if dimensions specified
    if width is not None and height is not None:
        if width <= 0 or height <= 0:
            return background
        overlay = cv2.resize(overlay, (int(width), int(height)), interpolation=cv2.INTER_AREA)

    h, w, c = overlay.shape
    bg_h, bg_w = background.shape[:2]

    # Calculate clipping bounds
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_w, x + w), min(bg_h, y + h)

    overlay_x1 = max(0, -x)
    overlay_y1 = max(0, -y)
    overlay_x2 = overlay_x1 + (x2 - x1)
    overlay_y2 = overlay_y1 + (y2 - y1)

    if x1 >= x2 or y1 >= y2 or overlay_x1 >= overlay_x2 or overlay_y1 >= overlay_y2:
        return background

    overlay_roi = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
    background_roi = background[y1:y2, x1:x2]

    if overlay_roi.shape[2] == 4:
        alpha = overlay_roi[:, :, 3] / 255.0
        alpha_inv = 1.0 - alpha
        for channel in range(3):
            background_roi[:, :, channel] = (
                alpha * overlay_roi[:, :, channel] +
                alpha_inv * background_roi[:, :, channel]
            )
    else:
        background_roi[:] = overlay_roi[:, :, :3]

    return background


class FaceFilterApp:
    def __init__(self):
        # Load Haar Cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError(f"Could not load Haar cascade from {cascade_path}")

        # Active filter: 'dog', 'cat', or None
        self.active_filter = 'dog'

        # Load transparent filter PNG assets (with UNCHANGED flag for alpha channel)
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.dog_ears = cv2.imread(os.path.join(assets_dir, 'dog_ears.png'), cv2.IMREAD_UNCHANGED)
        self.dog_nose = cv2.imread(os.path.join(assets_dir, 'dog_nose.png'), cv2.IMREAD_UNCHANGED)
        self.cat_ears = cv2.imread(os.path.join(assets_dir, 'cat_ears.png'), cv2.IMREAD_UNCHANGED)
        self.cat_nose = cv2.imread(os.path.join(assets_dir, 'cat_nose.png'), cv2.IMREAD_UNCHANGED)

        # Smoothed face coordinates for jitter reduction: (x, y, w, h)
        self.smoothed_faces = []
        self.smoothing_factor = 0.45  # Higher = faster tracking, lower = smoother

        # Snapshot notification timer
        self.notification_text = ""
        self.notification_expiry = 0

        # Create snapshots directory
        self.snapshot_dir = os.path.join(os.path.dirname(__file__), 'snapshots')
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def draw_hud(self, frame):
        """Draws a clean on-screen UI overlay with controls."""
        h, w = frame.shape[:2]

        # Top banner background
        cv2.rectangle(frame, (0, 0), (w, 52), (25, 25, 30), -1)
        cv2.line(frame, (0, 52), (w, 52), (60, 60, 70), 1)

        # Title and Current Filter Badge
        cv2.putText(frame, "FACE FILTERS", (16, 33),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (240, 240, 240), 1, cv2.LINE_AA)

        badge_text = f"Filter: {self.active_filter.upper() if self.active_filter else 'NONE'}"
        badge_color = (60, 180, 75) if self.active_filter == 'dog' else (
            (220, 120, 180) if self.active_filter == 'cat' else (130, 130, 130)
        )
        cv2.rectangle(frame, (200, 12), (360, 42), badge_color, -1)
        cv2.putText(frame, badge_text, (212, 33),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        # Controls instructions
        controls_text = "[1] Dog   [2] Cat   [0] None   [S] Snapshot   [Q] Quit"
        cv2.putText(frame, controls_text, (w - 490, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 205), 1, cv2.LINE_AA)

        # Snapshot notification toast
        if time.time() < self.notification_expiry:
            toast_w = 420
            tx1 = (w - toast_w) // 2
            cv2.rectangle(frame, (tx1, h - 55), (tx1 + toast_w, h - 18), (30, 160, 50), -1)
            cv2.putText(frame, self.notification_text, (tx1 + 15, h - 30),
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    def apply_filter(self, frame, x, y, w, h):
        """Applies ears and nose onto a detected face."""
        if self.active_filter == 'dog':
            # 1. Dog Ears
            ears_w = int(w * 1.25)
            ears_aspect = self.dog_ears.shape[0] / self.dog_ears.shape[1]
            ears_h = int(ears_w * ears_aspect)
            ears_x = x - int((ears_w - w) / 2)
            ears_y = y - int(ears_h * 0.55)
            frame = overlay_transparent(frame, self.dog_ears, ears_x, ears_y, ears_w, ears_h)

            # 2. Dog Snout & Tongue
            nose_w = int(w * 0.55)
            nose_aspect = self.dog_nose.shape[0] / self.dog_nose.shape[1]
            nose_h = int(nose_w * nose_aspect)
            nose_x = x + int(w / 2) - int(nose_w / 2)
            nose_y = y + int(h * 0.52)
            frame = overlay_transparent(frame, self.dog_nose, nose_x, nose_y, nose_w, nose_h)

        elif self.active_filter == 'cat':
            # 1. Cat Ears
            ears_w = int(w * 1.15)
            ears_aspect = self.cat_ears.shape[0] / self.cat_ears.shape[1]
            ears_h = int(ears_w * ears_aspect)
            ears_x = x - int((ears_w - w) / 2)
            ears_y = y - int(ears_h * 0.70)
            frame = overlay_transparent(frame, self.cat_ears, ears_x, ears_y, ears_w, ears_h)

            # 2. Cat Whiskers & Nose
            nose_w = int(w * 0.82)
            nose_aspect = self.cat_nose.shape[0] / self.cat_nose.shape[1]
            nose_h = int(nose_w * nose_aspect)
            nose_x = x + int(w / 2) - int(nose_w / 2)
            nose_y = y + int(h * 0.55)
            frame = overlay_transparent(frame, self.cat_nose, nose_x, nose_y, nose_w, nose_h)

        return frame

    def run(self):
        print("\nOpening camera...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW enables fast camera startup on Windows
        if not cap.isOpened():
            # Fallback to standard backend if DSHOW fails
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("ERROR: Could not access the webcam.")
            print("Please ensure your camera is connected and not in use by another app.")
            return

        # Set standard 720p or 480p resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        print("\nFace Filter App is running!")
        print("Hotkeys:")
        print("  [1] Dog Filter")
        print("  [2] Cat Filter")
        print("  [0] Remove Filter")
        print("  [S] Take Photo Snapshot")
        print("  [Q] or [ESC] to Quit\n")

        prev_box = None

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from camera.")
                break

            # Mirror view for intuitive webcam interaction
            frame = cv2.flip(frame, 1)

            # Convert to grayscale for Haar face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.18,
                minNeighbors=5,
                minSize=(90, 90)
            )

            # Process primary face with smoothing
            if len(faces) > 0:
                # Pick largest face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                fx, fy, fw, fh = largest_face

                if prev_box is None:
                    prev_box = [fx, fy, fw, fh]
                else:
                    # Exponential Moving Average for buttery smooth tracking
                    prev_box[0] = int(self.smoothing_factor * fx + (1 - self.smoothing_factor) * prev_box[0])
                    prev_box[1] = int(self.smoothing_factor * fy + (1 - self.smoothing_factor) * prev_box[1])
                    prev_box[2] = int(self.smoothing_factor * fw + (1 - self.smoothing_factor) * prev_box[2])
                    prev_box[3] = int(self.smoothing_factor * fh + (1 - self.smoothing_factor) * prev_box[3])

                frame = self.apply_filter(frame, *prev_box)
            else:
                prev_box = None

            # Draw HUD
            self.draw_hud(frame)

            # Show window
            cv2.imshow("Face Filters - Dog & Cat", frame)

            # Key handling
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 27 is ESC
                break
            elif key == ord('1'):
                self.active_filter = 'dog'
            elif key == ord('2'):
                self.active_filter = 'cat'
            elif key == ord('0'):
                self.active_filter = None
            elif key == ord('s') or key == ord('S'):
                filename = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                save_path = os.path.join(self.snapshot_dir, filename)
                cv2.imwrite(save_path, frame)
                self.notification_text = f"Saved: {filename}"
                self.notification_expiry = time.time() + 2.5
                print(f"[Snapshot Captured] -> {save_path}")

        cap.release()
        cv2.destroyAllWindows()
        print("Camera closed. Goodbye!")


if __name__ == "__main__":
    app = FaceFilterApp()
    app.run()
