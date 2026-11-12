"""
Builds the standalone web/index.html with embedded base64 assets and MediaPipe tracking.
"""

import os
import base64

def get_b64(path):
    with open(path, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')

dog_ears_b64 = get_b64('assets/dog_ears.png')
dog_nose_b64 = get_b64('assets/dog_nose.png')
cat_ears_b64 = get_b64('assets/cat_ears.png')
cat_nose_b64 = get_b64('assets/cat_nose.png')

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Face Filters - Dog & Cat Camera App</title>
  <!-- MediaPipe FaceMesh & Camera Utils -->
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js" crossorigin="anonymous"></script>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }}
    body {{
      background: #0f111a;
      color: #f0f2f5;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
    }}
    .app-container {{
      position: relative;
      width: 90vw;
      max-width: 960px;
      aspect-ratio: 16 / 9;
      background: #181a24;
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.1);
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    #webcam {{
      display: none;
    }}
    #canvas {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transform: scaleX(-1); /* Mirror camera for natural feel */
    }}
    .loading-overlay {{
      position: absolute;
      inset: 0;
      background: rgba(15, 17, 26, 0.9);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      z-index: 10;
      transition: opacity 0.4s ease;
    }}
    .loading-overlay.hidden {{
      opacity: 0;
      pointer-events: none;
    }}
    .spinner {{
      width: 48px;
      height: 48px;
      border: 4px solid rgba(255, 255, 255, 0.15);
      border-top-color: #6366f1;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }}
    @keyframes spin {{
      to {{ transform: rotate(360deg); }}
    }}
    .controls-bar {{
      margin-top: 20px;
      display: flex;
      align-items: center;
      gap: 14px;
      background: rgba(24, 26, 36, 0.85);
      padding: 12px 20px;
      border-radius: 40px;
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    .btn {{
      appearance: none;
      border: none;
      background: rgba(255, 255, 255, 0.08);
      color: #e2e8f0;
      font-size: 15px;
      font-weight: 600;
      padding: 10px 20px;
      border-radius: 25px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .btn:hover {{
      background: rgba(255, 255, 255, 0.16);
      transform: translateY(-2px);
    }}
    .btn.active {{
      background: #6366f1;
      color: #ffffff;
      box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
    }}
    .btn-snap {{
      background: #ef4444;
      color: white;
      padding: 10px 24px;
    }}
    .btn-snap:hover {{
      background: #dc2626;
      box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
    }}
    .toast {{
      position: absolute;
      top: 24px;
      background: rgba(16, 185, 129, 0.95);
      color: white;
      padding: 10px 22px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 14px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
      opacity: 0;
      transform: translateY(-10px);
      transition: all 0.3s ease;
      z-index: 20;
      pointer-events: none;
    }}
    .toast.show {{
      opacity: 1;
      transform: translateY(0);
    }}
  </style>
</head>
<body>

  <div class="app-container">
    <video id="webcam" playsinline></video>
    <canvas id="canvas"></canvas>
    <div id="toast" class="toast">📸 Photo Captured!</div>
    <div id="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p id="loading-text">Starting Camera & AI Face Tracking...</p>
    </div>
  </div>

  <div class="controls-bar">
    <button id="btn-dog" class="btn active" onclick="setFilter('dog')">
      🐶 Dog Filter
    </button>
    <button id="btn-cat" class="btn" onclick="setFilter('cat')">
      🐱 Cat Filter
    </button>
    <button id="btn-none" class="btn" onclick="setFilter('none')">
      🚫 None
    </button>
    <div style="width: 1px; height: 24px; background: rgba(255,255,255,0.15); margin: 0 4px;"></div>
    <button id="btn-snap" class="btn btn-snap" onclick="takeSnapshot()">
      📸 Snap Photo
    </button>
  </div>

  <script>
    // Asset Images (Base64)
    const assets = {{
      dogEars: new Image(),
      dogNose: new Image(),
      catEars: new Image(),
      catNose: new Image()
    }};
    assets.dogEars.src = "{dog_ears_b64}";
    assets.dogNose.src = "{dog_nose_b64}";
    assets.catEars.src = "{cat_ears_b64}";
    assets.catNose.src = "{cat_nose_b64}";

    let currentFilter = 'dog';
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const loading = document.getElementById('loading');
    const toast = document.getElementById('toast');

    function setFilter(filter) {{
      currentFilter = filter;
      document.querySelectorAll('.controls-bar .btn').forEach(btn => {{
        if (btn.id !== 'btn-snap') btn.classList.remove('active');
      }});
      if (filter === 'dog') document.getElementById('btn-dog').classList.add('active');
      if (filter === 'cat') document.getElementById('btn-cat').classList.add('active');
      if (filter === 'none') document.getElementById('btn-none').classList.add('active');
    }}

    function showToast(msg) {{
      toast.textContent = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2200);
    }}

    function takeSnapshot() {{
      const link = document.createElement('a');
      link.download = `face_filter_${{currentFilter}}_${{Date.now()}}.png`;
      // We flip the canvas horizontally for the saved snapshot so it matches the mirror preview
      const offscreen = document.createElement('canvas');
      offscreen.width = canvas.width;
      offscreen.height = canvas.height;
      const oCtx = offscreen.getContext('2d');
      oCtx.translate(canvas.width, 0);
      oCtx.scale(-1, 1);
      oCtx.drawImage(canvas, 0, 0);
      link.href = offscreen.toDataURL('image/png');
      link.click();
      showToast('📸 Snapshot Downloaded!');
    }}

    function onResults(results) {{
      loading.classList.add('hidden');

      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;

      // Draw camera frame
      ctx.save();
      ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

      if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0 && currentFilter !== 'none') {{
        for (const landmarks of results.multiFaceLandmarks) {{
          drawFilter(landmarks);
        }}
      }}
      ctx.restore();
    }}

    function drawFilter(lm) {{
      const w = canvas.width;
      const h = canvas.height;

      // Key landmark points:
      // Forehead / top head: 10
      // Chin: 152
      // Left eye corner: 33, Right eye corner: 263
      // Nose tip: 1
      // Upper lip: 13, Lower lip: 14
      const forehead = {{ x: lm[10].x * w, y: lm[10].y * h }};
      const chin = {{ x: lm[152].x * w, y: lm[152].y * h }};
      const leftEye = {{ x: lm[33].x * w, y: lm[33].y * h }};
      const rightEye = {{ x: lm[263].x * w, y: lm[263].y * h }};
      const nose = {{ x: lm[1].x * w, y: lm[1].y * h }};
      const upperLip = {{ x: lm[13].x * w, y: lm[13].y * h }};
      const lowerLip = {{ x: lm[14].x * w, y: lm[14].y * h }};

      // Face scale and rotation angle
      const dx = rightEye.x - leftEye.x;
      const dy = rightEye.y - leftEye.y;
      const eyeDist = Math.hypot(dx, dy);
      const angle = Math.atan2(dy, dx);
      const faceWidth = eyeDist * 2.3;

      // Check if mouth is open
      const mouthOpenDist = Math.hypot(lowerLip.x - upperLip.x, lowerLip.y - upperLip.y);
      const mouthOpen = mouthOpenDist > (eyeDist * 0.22);

      if (currentFilter === 'dog') {{
        // 1. Draw Dog Ears
        const earsW = faceWidth * 1.35;
        const earsH = earsW * (assets.dogEars.height / assets.dogEars.width);

        ctx.save();
        ctx.translate(forehead.x, forehead.y);
        ctx.rotate(angle);
        ctx.drawImage(assets.dogEars, -earsW / 2, -earsH * 0.55, earsW, earsH);
        ctx.restore();

        // 2. Draw Dog Snout & Tongue
        let noseW = faceWidth * 0.60;
        let noseH = noseW * (assets.dogNose.height / assets.dogNose.width);
        if (mouthOpen) {{
          // Animate / stretch tongue when mouth opens!
          noseH *= 1.15;
        }}

        ctx.save();
        ctx.translate(nose.x, nose.y);
        ctx.rotate(angle);
        ctx.drawImage(assets.dogNose, -noseW / 2, -noseH * 0.35, noseW, noseH);
        ctx.restore();

      }} else if (currentFilter === 'cat') {{
        // 1. Draw Cat Ears
        const earsW = faceWidth * 1.25;
        const earsH = earsW * (assets.catEars.height / assets.catEars.width);

        ctx.save();
        ctx.translate(forehead.x, forehead.y);
        ctx.rotate(angle);
        ctx.drawImage(assets.catEars, -earsW / 2, -earsH * 0.72, earsW, earsH);
        ctx.restore();

        // 2. Draw Cat Whiskers & Nose
        const noseW = faceWidth * 0.90;
        const noseH = noseW * (assets.catNose.height / assets.catNose.width);

        ctx.save();
        ctx.translate(nose.x, nose.y);
        ctx.rotate(angle);
        ctx.drawImage(assets.catNose, -noseW / 2, -noseH * 0.45, noseW, noseH);
        ctx.restore();
      }}
    }}

    async function initCamera() {{
      try {{
        const stream = await navigator.mediaDevices.getUserMedia({{
          video: {{ width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }},
          audio: false
        }});
        video.srcObject = stream;
        await video.play();

        const faceMesh = new FaceMesh({{
          locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${{file}}`
        }});

        faceMesh.setOptions({{
          maxNumFaces: 2,
          refineLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        }});

        faceMesh.onResults(onResults);

        const camera = new Camera(video, {{
          onFrame: async () => {{
            await faceMesh.send({{ image: video }});
          }},
          width: 1280,
          height: 720
        }});

        camera.start();
      }} catch (err) {{
        console.error("Camera access error:", err);
        document.getElementById('loading-text').textContent =
          "Please grant camera access to use face filters!";
      }}
    }}

    window.addEventListener('load', initCamera);
  </script>
</body>
</html>
'''

os.makedirs('web', exist_ok=True)
with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("web/index.html created successfully!")
