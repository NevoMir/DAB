import cv2
import os
import time
import sys
import threading
import socket

# Try to import flask for the web streaming part.
# If not available, we can just skip the web server part or warn.
try:
    from flask import Flask, Response, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    print("Warning: flask library not found. Web/local network streaming will be disabled.")
    FLASK_AVAILABLE = False

# ==========================================
# PART 1: USB Camera Class & Web Streaming
# ==========================================

app = Flask(__name__) if FLASK_AVAILABLE else None

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
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"Failed to open USB Camera at index {self.camera_index}")
                return False
            
            # Set resolution (optional)
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
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error reading from USB Camera: {e}")
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

# Global camera instance for Flask to access
global_camera = None

def generate_frames():
    global global_camera
    if not global_camera:
        return

    while True:
        frame = global_camera.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
            
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)

if FLASK_AVAILABLE:
    @app.route('/')
    def index():
        return render_template_string("""
        <html>
            <head>
                <title>Pi Camera Stream</title>
                <style>
                    body { font-family: sans-serif; text-align: center; background: #222; color: #fff; }
                    img { border: 2px solid #555; max-width: 100%; height: auto; }
                </style>
            </head>
            <body>
                <h1>Raspberry Pi Camera Stream</h1>
                <img src="{{ url_for('video_feed') }}">
            </body>
        </html>
        """)

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def run_flask():
    if not FLASK_AVAILABLE:
        return
    ip = get_ip_address()
    print(f"\nStream available at: http://{ip}:5000\n")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"Flask server error: {e}")

# ==========================================
# PART 2: Slideshow Logic
# ==========================================

def resize_image_to_fit_screen(img, screen_w, screen_h):
    h, w = img.shape[:2]
    scale = min(screen_w/w, screen_h/h)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h))

def overlay_camera(background, cam_frame, scale=0.3, padding=20):
    if cam_frame is None:
        return background
    
    bg_h, bg_w = background.shape[:2]
    
    # Resize camera frame
    cam_h, cam_w = cam_frame.shape[:2]
    cam_scale = min((bg_w * scale) / cam_w, (bg_h * scale) / cam_h)
    new_cam_w = int(cam_w * cam_scale)
    new_cam_h = int(cam_h * cam_scale)
    resized_cam = cv2.resize(cam_frame, (new_cam_w, new_cam_h))
    
    # Define position (Bottom Right)
    x_offset = bg_w - new_cam_w - padding
    y_offset = bg_h - new_cam_h - padding
    
    # Ensure it fits
    if x_offset < 0: x_offset = 0
    if y_offset < 0: y_offset = 0
    
    # Overlay
    background[y_offset:y_offset+new_cam_h, x_offset:x_offset+new_cam_w] = resized_cam
    
    # Add a border
    cv2.rectangle(
        background,
        (x_offset, y_offset),
        (x_offset+new_cam_w, y_offset+new_cam_h),
        (255, 255, 255),
        2
    )
    
    return background

def main():
    global global_camera
    
    # 1. Start Camera
    # Try index 0 first, if fails try others
    camera_idx = 0
    cam = USBCameraStream(camera_idx)
    if not cam.start():
        # Fallback scan
        print("Camera 0 failed, scanning...")
        for i in range(1, 4):
            temp_cam = USBCameraStream(i)
            if temp_cam.start():
                cam = temp_cam
                print(f"Found camera at index {i}")
                break
            
    if not cam.running:
        print("No camera could be started. Slideshow will run without camera.")
        global_camera = None
    else:
        global_camera = cam
    
    # 2. Start Flask Server in Background Thread
    if FLASK_AVAILABLE and global_camera:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

    # 3. Prepare Slideshow
    image_folder = 'images'
    if not os.path.exists(image_folder):
        print(f"Error: Folder '{image_folder}' not found.")
        return

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(valid_extensions)]
    images.sort()

    if not images:
        print("No images found for slideshow.")
        return

    window_name = 'Slideshow + Camera'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Controls:")
    print("  'q' - Quit")
    print("  'n' - Next image")

    curr_img_idx = 0
    start_time = time.time()
    slide_duration = 3.0 # seconds
    
    # Load first image
    current_bg = cv2.imread(os.path.join(image_folder, images[curr_img_idx]))
    if current_bg is None:
        print("Failed to load first image.")
        return # Or handle more gracefully

    # Determine screen resolution? 
    # cv2.WINDOW_FULLSCREEN usually handles it, but for resizing we might want to know
    # We'll just rely on the image size or a fixed size if needed. 
    # Better: just use the image size, or resize image to a standard 1920x1080 if not matching.
    # For simplicity, we just display the image at its native resolution or maximized.
    
    try:
        while True:
            # Check time to switch slides
            if time.time() - start_time > slide_duration:
                curr_img_idx = (curr_img_idx + 1) % len(images)
                new_img_path = os.path.join(image_folder, images[curr_img_idx])
                temp_img = cv2.imread(new_img_path)
                if temp_img is not None:
                    current_bg = temp_img
                start_time = time.time()
            
            # Create a copy to draw on
            display_frame = current_bg.copy()
            
            # Get camera frame
            cam_frame = None
            if global_camera:
                cam_frame = global_camera.get_frame()
            
            # Overlay
            if cam_frame is not None:
                display_frame = overlay_camera(display_frame, cam_frame)
            
            # Show
            cv2.imshow(window_name, display_frame)
            
            # Wait a bit (approx 30 fps)
            key = cv2.waitKey(30)
            
            if key == ord('q'):
                break
            elif key == ord('n'):
                # Manual next
                curr_img_idx = (curr_img_idx + 1) % len(images)
                new_img_path = os.path.join(image_folder, images[curr_img_idx])
                temp_img = cv2.imread(new_img_path)
                if temp_img is not None:
                    current_bg = temp_img
                start_time = time.time()

    except KeyboardInterrupt:
        pass
    finally:
        print("Cleaning up...")
        if global_camera:
            global_camera.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
