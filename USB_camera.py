import time
import threading
import cv2
import socket

try:
    from flask import Flask, Response, render_template_string
except ImportError:
    print("Error: flask library not found. Please run: pip install flask")
    exit(1)

app = Flask(__name__)

class USBCameraStream:
    def __init__(self, camera_index):
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.thread = None
        self.frame = None
        self.lock = threading.Lock()

    def start(self):
        try:
            print(f"Initializing USB Camera at index {self.camera_index}...")
            # Open the camera
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"Failed to open USB Camera at index {self.camera_index}")
                return False
            
            # Set resolution (optional, but good for performance)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"USB Camera {self.camera_index} started.")
            return True
        except Exception as e:
            print(f"Error starting USB Camera {self.camera_index}: {e}")
            return False

    def _update(self):
        while self.running and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                else:
                    # If we can't read, maybe the camera was unplugged
                    print(f"Failed to read frame from USB Camera {self.camera_index}")
                    time.sleep(1)
            except Exception as e:
                print(f"Error reading from USB Camera {self.camera_index}: {e}")
                time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()

# Global camera objects
cameras = {}

def generate_frames(camera_index):
    cam = cameras.get(camera_index)
    if not cam:
        return

    while True:
        frame = cam.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
            
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Yield the frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Limit frame rate
        time.sleep(0.03)

@app.route('/')
def index():
    # Check which cameras are actually running
    active_cams = [idx for idx, cam in cameras.items() if cam.running]
    
    html = """
    <html>
        <head>
            <title>Pi 5 USB Camera Stream</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #222; color: #fff; }
                .container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-top: 20px; }
                .cam-box { background: #333; padding: 10px; border-radius: 8px; }
                img { border: 2px solid #555; max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Raspberry Pi 5 USB Camera</h1>
            <div class="container">
                {% for cam_idx in active_cams %}
                <div class="cam-box">
                    <h3>USB Camera {{ cam_idx }}</h3>
                    <img src="{{ url_for('video_feed', cam_idx=cam_idx) }}">
                </div>
                {% else %}
                <div class="cam-box">
                    <h3>No USB Cameras Detected</h3>
                    <p>Please check connections and restart script.</p>
                </div>
                {% endfor %}
            </div>
        </body>
    </html>
    """
    return render_template_string(html, active_cams=active_cams)

@app.route('/video_feed/<int:cam_idx>')
def video_feed(cam_idx):
    return Response(generate_frames(cam_idx),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def find_usb_cameras():
    # Try to find available USB cameras by testing indices
    # We'll test indices 0 to 10. If we open it, we assume it's valid.
    # Note: This might pick up CSI cameras if they are registered as video nodes (e.g. /dev/video0)
    # but usually on Pi 5 with libcamera, standard cv2.VideoCapture(0) might fail for CSI 
    # unless using libcamerify or specific backend. For USB it should just work.
    
    found_cameras = []
    print("Scanning for USB cameras (indices 0-9)...")
    
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Read a frame to be sure
            ret, _ = cap.read()
            if ret:
                print(f"  Found camera at index {i}")
                found_cameras.append(i)
            cap.release()
            
    return found_cameras

if __name__ == "__main__":
    # Scan for cameras
    available_indices = find_usb_cameras()
    
    if not available_indices:
        print("No cameras found during scan. Attempting default index 0 anyway...")
        available_indices = [0]

    # Initialize cameras
    for idx in available_indices:
        cam = USBCameraStream(idx)
        if cam.start():
            cameras[idx] = cam

    if not cameras:
        print("Could not start any cameras.")
    else:
        ip = get_ip_address()
        print(f"\n\n=================================================")
        print(f"  USB STREAMING STARTED")
        print(f"  Open this link in your browser:")
        print(f"  http://{ip}:5000")
        print(f"=================================================\n\n")

        try:
            app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        finally:
            print("Stopping cameras...")
            for cam in cameras.values():
                cam.stop()
