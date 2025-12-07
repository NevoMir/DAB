import time
import threading
import cv2
import socket
try:
    from picamera2 import Picamera2
except ImportError:
    print("Error: picamera2 library not found. Please install it.")
    exit(1)

try:
    from flask import Flask, Response, render_template_string
except ImportError:
    print("Error: flask library not found. Please run: pip install flask")
    exit(1)

app = Flask(__name__)

class CameraStream:
    def __init__(self, camera_num):
        self.camera_num = camera_num
        self.picam2 = None
        self.running = False
        self.thread = None
        self.frame = None
        self.lock = threading.Lock()

    def start(self):
        try:
            print(f"Initializing Camera {self.camera_num}...")
            self.picam2 = Picamera2(camera_num=self.camera_num)
            
            # Configure camera for video capture
            # Lower resolution for smoother network streaming
            config = self.picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
            self.picam2.configure(config)
            self.picam2.start()
            
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"Camera {self.camera_num} started.")
            return True
        except IndexError:
            print(f"Camera {self.camera_num} not found.")
            return False
        except Exception as e:
            print(f"Failed to start Camera {self.camera_num}: {e}")
            return False

    def _update(self):
        while self.running:
            try:
                # capture_array returns the image as a numpy array
                image = self.picam2.capture_array()
                
                if image is not None:
                    # Picamera2 XRGB8888 is actually BGRX (BGRA)
                    # OpenCV expects BGR.
                    if image.shape[2] == 4:
                        # Drop alpha channel, keep BGR order
                        frame = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                    else:
                        # Fallback if format changes
                        frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    with self.lock:
                        self.frame = frame
                        
            except Exception as e:
                print(f"Error reading from Camera {self.camera_num}: {e}")
                time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()

# Global camera objects
cameras = {}

def generate_frames(camera_num):
    cam = cameras.get(camera_num)
    if not cam:
        return

    while True:
        frame = cam.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
            
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Yield the frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Limit frame rate slightly to save bandwidth
        time.sleep(0.03)

@app.route('/')
def index():
    # Check which cameras are actually running
    active_cams = [num for num, cam in cameras.items() if cam.running]
    
    html = """
    <html>
        <head>
            <title>Pi 5 Camera Stream</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #222; color: #fff; }
                .container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-top: 20px; }
                .cam-box { background: #333; padding: 10px; border-radius: 8px; }
                img { border: 2px solid #555; max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Raspberry Pi 5 CSI Cameras</h1>
            <div class="container">
                {% for cam_num in active_cams %}
                <div class="cam-box">
                    <h3>Camera {{ cam_num }}</h3>
                    <img src="{{ url_for('video_feed', cam_num=cam_num) }}">
                </div>
                {% else %}
                <div class="cam-box">
                    <h3>No Cameras Detected</h3>
                    <p>Please check connections and restart script.</p>
                </div>
                {% endfor %}
            </div>
        </body>
    </html>
    """
    return render_template_string(html, active_cams=active_cams)

@app.route('/video_feed/<int:cam_num>')
def video_feed(cam_num):
    return Response(generate_frames(cam_num),
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

if __name__ == "__main__":
    # Initialize cameras
    cameras[0] = CameraStream(0)
    cameras[1] = CameraStream(1)

    # Start them
    cameras[0].start()
    cameras[1].start()

    ip = get_ip_address()
    print(f"\n\n=================================================")
    print(f"  STREAMING STARTED")
    print(f"  Open this link in your browser:")
    print(f"  http://{ip}:5000")
    print(f"=================================================\n\n")

    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        print("Stopping cameras...")
        cameras[0].stop()
        cameras[1].stop()
