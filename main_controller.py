import time
import threading
import socket
import cv2
import board
import neopixel
import os
import sys
from flask import Flask, Response, render_template_string
from gpiozero import Button
from adafruit_servokit import ServoKit
from rgb1602 import RGB1602

# Import CSI Camera Class (Keep this as it seems to work for CSI)
try:
    from CSI_camera import CameraStream as CSICameraStream
except ImportError:
    print("Error: Could not import CameraStream (CSI)")

# REDEFINE USB CAMERA CLASS LOCALLY
# This allows us to add custom error handling (suppress spam) without modifying the user's original file.
class USBCameraStream:
    def __init__(self, camera_index):
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.thread = None
        self.frame = None
        self.lock = threading.Lock()
        self.error_count = 0 

    def start(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False
            # Try to read one frame to ensure it's real
            ret, _ = self.cap.read()
            if not ret:
                return False
                
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            # print(f"Error starting USB Camera {self.camera_index}: {e}")
            return False

    def _update(self):
        while self.running and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                    self.error_count = 0 # Reset error count on success
                else:
                    self.error_count += 1
                    # Only print the error once every 100 failures to avoid spam
                    if self.error_count % 100 == 1:
                         print(f"Warning: USB Camera {self.camera_index} failed to read frame (Count: {self.error_count})")
                    time.sleep(0.1)
                    
                    # Optional: Stop if too many errors?
                    # if self.error_count > 500: self.running = False
            except Exception:
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


# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================
LED_PIN_1 = board.D12
LED_COUNT_1 = 120
LED_PIN_2 = board.D18
LED_COUNT_2 = 32

BUTTON_PIN = 4
IMAGE_FOLDER = 'images'

# Global State
system_running = threading.Event()
app = Flask(__name__)
active_cameras = {}

# ==============================================================================
# FLASK APP
# ==============================================================================
def generate_frames(cam_key):
    cam = active_cameras.get(cam_key)
    if not cam: return
    while True:
        frame = cam.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret: continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.04) 

@app.route('/')
def index():
    active_keys = sorted(list(active_cameras.keys()))
    html = """
    <html>
        <head>
            <title>DAB Controller Stream</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #222; color: #fff; }
                .container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-top: 20px; }
                .cam-box { background: #333; padding: 10px; border-radius: 8px; }
                img { border: 2px solid #555; max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Live Camera Feeds</h1>
            <div class="container">
                {% for key in active_keys %}
                <div class="cam-box">
                    <h3>{{ key }}</h3>
                    <img src="{{ url_for('video_feed', cam_key=key) }}">
                </div>
                {% else %}
                <p>No cameras active.</p>
                {% endfor %}
            </div>
        </body>
    </html>
    """
    return render_template_string(html, active_keys=active_keys)

@app.route('/video_feed/<cam_key>')
def video_feed(cam_key):
    return Response(generate_frames(cam_key),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ==============================================================================
# LED CONTROLLER
# ==============================================================================
class LEDController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.pixels_1 = neopixel.NeoPixel(LED_PIN_1, LED_COUNT_1, brightness=0.2, auto_write=False)
        self.pixels_2 = neopixel.NeoPixel(LED_PIN_2, LED_COUNT_2, brightness=0.2, auto_write=False)

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def _animate(self):
        colors = [
            ((255, 0, 0), (0, 0, 255)), # Red / Blue
            ((0, 255, 0), (255, 0, 0)), # Green / Red
            ((0, 0, 255), (0, 255, 0)), # Blue / Green
            ((255, 255, 255), (255, 255, 255)) # White
        ]
        while self.running:
            for c1, c2 in colors:
                if not self.running: break
                self.pixels_1.fill(c1)
                self.pixels_2.fill(c2)
                self.pixels_1.show()
                self.pixels_2.show()
                # Sleep in small chunks to be responsive to stop
                for _ in range(10): 
                    if not self.running: break
                    time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.thread: 
            self.thread.join()
            self.thread = None
        # Turn off
        try:
            self.pixels_1.fill((0,0,0)); self.pixels_1.show()
            self.pixels_2.fill((0,0,0)); self.pixels_2.show()
        except: pass

# ==============================================================================
# SERVO CONTROLLER
# ==============================================================================
class ServoController:
    def __init__(self, kit):
        self.kit = kit
        self.running = False
        self.thread = None
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        servo = self.kit.servo[0]
        # Reset
        servo.angle = 0
        time.sleep(1)
        
        while self.running:
            # 0 -> 180
            self._move_smoothly(servo, 0, 180, 4.0)
            if not self.running: break
            time.sleep(1)
            # 180 -> 0
            self._move_smoothly(servo, 180, 0, 5.0)
            if not self.running: break
            time.sleep(1)

    def _move_smoothly(self, servo, start, end, duration):
        freq = 50
        steps = int(duration * freq)
        delay = 1.0 / freq
        step_val = (end - start) / steps
        current = start
        for _ in range(steps):
            if not self.running: return
            current += step_val
            if current < 0: current = 0
            if current > 180: current = 180
            servo.angle = current
            time.sleep(delay)
        servo.angle = end

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None

# ==============================================================================
# MAIN LOGIC
# ==============================================================================
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def toggle_system():
    if system_running.is_set():
        print("Stopping System...")
        system_running.clear()
    else:
        print("Starting System...")
        system_running.set()

def main():
    # 1. Hardware Init
    lcd = None
    try:
        lcd = RGB1602(16, 2)
        lcd.setRGB(255, 255, 255)
    except: print("LCD Init Failed (Check I2C)")

    button = Button(BUTTON_PIN, pull_up=False)
    button.when_pressed = toggle_system

    kit = None
    try:
        kit = ServoKit(channels=16)
    except: print("ServoKit Init Failed (Check I2C)")

    # Controllers
    led_ctrl = LEDController()
    servo_ctrl = ServoController(kit) if kit else None

    # 2. Start Cameras & Flask (Available always)
    
    # CSI
    for i in range(2):
        try:
            cam = CSICameraStream(i)
            if cam.start(): active_cameras[f"CSI Camera {i}"] = cam
        except: pass
    
    # START USB CAMERAS
    print("Attempting to start USB Cameras (scanning 0-9)...")
    for i in range(10): 
        try:
            cam = USBCameraStream(i)
            # Custom 'start' now includes a robust frame check
            if cam.start():
                print(f"  -> USB Camera {i} is VALID.")
                active_cameras[f"USB Camera {i}"] = cam
            else:
                pass 
        except Exception as e:
            pass

    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    # 3. Slideshow Setup
    images = []
    if os.path.exists(IMAGE_FOLDER):
        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        images = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(exts)]
        images.sort()
    
    # Check Display Environment for Sudos
    if "DISPLAY" not in os.environ:
        print("Warning: DISPLAY environment variable not set. Slideshow/GUI might fail.")
        print("Try: export DISPLAY=:0 && sudo -E python3 main_controller.py")
        # Attempt to auto-fix
        os.environ["DISPLAY"] = ":0"
    
    window_name = "Slideshow"
    current_img_idx = 0
    slideshow_enabled = True # Fallback if GUI fails
    
    print(f"\nReady. IP: {get_ip_address()}")
    print("Press Button to Start/Stop. Ctrl+C to Exit.\n")

    # Initial LCD
    if lcd:
        lcd.clear()
        lcd.setCursor(0,0); lcd.print("Hello! To start")
        lcd.setCursor(0,1); lcd.print("press ---->")
        lcd.setRGB(255, 255, 255)

    last_state = False 
    last_slide_time = 0
    SLIDE_DURATION = 3.0

    try:
        while True:
            if system_running.is_set():
                # --- RUNNING STATE ---
                if not last_state:
                    if lcd:
                        lcd.clear()
                        lcd.setCursor(0,0); lcd.print("Running...")
                        lcd.setCursor(0,1); lcd.print(get_ip_address())
                        lcd.setRGB(0, 255, 0)
                    led_ctrl.start()
                    if servo_ctrl: servo_ctrl.start()
                    
                    # Try Open Window
                    try:
                        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                        slideshow_enabled = True
                    except Exception as e:
                        print(f"GUI Error: {e}. Slideshow disabled.")
                        slideshow_enabled = False
                        
                    last_state = True

                # Slideshow Logic
                if images and slideshow_enabled:
                    now = time.time()
                    if now - last_slide_time > SLIDE_DURATION:
                         # Load next image
                        img = cv2.imread(images[current_img_idx])
                        if img is not None:
                            try:
                                cv2.imshow(window_name, img)
                            except:
                                # If display disconnects mid-stream
                                slideshow_enabled = False
                        
                        current_img_idx = (current_img_idx + 1) % len(images)
                        last_slide_time = now
                
                # Critical: process GUI events
                if slideshow_enabled:
                    key = cv2.waitKey(100) 
                    if key == ord('q'):
                        system_running.clear() 
                else:
                    time.sleep(0.1)

            else:
                # --- IDLE STATE ---
                if last_state:
                    if lcd:
                        lcd.clear()
                        lcd.setCursor(0,0); lcd.print("Hello! To start")
                        lcd.setCursor(0,1); lcd.print("press ---->")
                        lcd.setRGB(255, 255, 255)
                    
                    led_ctrl.stop()
                    if servo_ctrl: servo_ctrl.stop()
                    
                    if slideshow_enabled:
                         try:
                             cv2.destroyAllWindows()
                             cv2.waitKey(1)
                         except: pass
                    
                    last_state = False

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        led_ctrl.stop()
        if servo_ctrl: servo_ctrl.stop()
        for cam in active_cameras.values():
            cam.stop()
        if lcd:
            try: lcd.clear(); lcd.setRGB(0,0,0)
            except: pass
        try:
             cv2.destroyAllWindows()
        except: pass

if __name__ == "__main__":
    main()
