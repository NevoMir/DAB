import time
import threading
import cv2
import socket
import board
import neopixel
import os
import sys
from flask import Flask, Response, render_template_string
from gpiozero import Button
from adafruit_servokit import ServoKit
from rgb1602 import RGB1602

# Import User's Camera Classes
try:
    from USB_camera import USBCameraStream
except ImportError:
    print("Error: Could not import USBCameraStream")

try:
    from CSI_camera import CameraStream as CSICameraStream
except ImportError:
    print("Error: Could not import CameraStream (CSI)")

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
                time.sleep(1)

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
    except: print("LCD Init Failed")

    button = Button(BUTTON_PIN, pull_up=False)
    button.when_pressed = toggle_system

    kit = None
    try:
        kit = ServoKit(channels=16)
    except: print("ServoKit Init Failed")

    # Controllers
    led_ctrl = LEDController()
    servo_ctrl = ServoController(kit) if kit else None

    # 2. Start Cameras & Flask (Available always, but maybe we only want to show them when running?)
    # User said "cameras should be all streaming". Usually this implies always available or available when running.
    # To avoid complexity of start/stop latency for cameras, we'll keep them running in background.
    
    # CSI
    for i in range(2):
        try:
            cam = CSICameraStream(i)
            if cam.start(): active_cameras[f"CSI Camera {i}"] = cam
        except: pass
    
    # USB
    for i in range(5):
        try:
            cam = USBCameraStream(i)
            if cam.start(): 
                active_cameras[f"USB Camera {i}"] = cam
                time.sleep(0.5)
        except: pass

    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    # 3. Slideshow Setup
    images = []
    if os.path.exists(IMAGE_FOLDER):
        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        images = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(exts)]
        images.sort()
    
    window_name = "Slideshow"
    current_img_idx = 0
    
    print(f"\nReady. IP: {get_ip_address()}")
    print("Press Button to Start/Stop. Ctrl+C to Exit.\n")

    # Initial LCD
    if lcd:
        lcd.clear()
        lcd.setCursor(0,0); lcd.print("Hello! To start")
        lcd.setCursor(0,1); lcd.print("press ---->")
        lcd.setRGB(255, 255, 255)

    last_state = False # To detect edges in main loop if needed, but event handles it.

    last_slide_time = 0
    SLIDE_DURATION = 3.0

    try:
        while True:
            if system_running.is_set():
                # --- RUNNING STATE ---
                
                # Check if we just started
                if not last_state:
                    # Just transitioned to ON
                    if lcd:
                        lcd.clear()
                        lcd.setCursor(0,0); lcd.print("Running...")
                        lcd.setCursor(0,1); lcd.print(get_ip_address())
                        lcd.setRGB(0, 255, 0)
                    led_ctrl.start()
                    if servo_ctrl: servo_ctrl.start()
                    
                    # Open Window
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    last_state = True

                # Slideshow Logic
                if images:
                    now = time.time()
                    if now - last_slide_time > SLIDE_DURATION:
                         # Load next image
                        img = cv2.imread(images[current_img_idx])
                        if img is not None:
                            cv2.imshow(window_name, img)
                        
                        current_img_idx = (current_img_idx + 1) % len(images)
                        last_slide_time = now
                
                # Critical: process GUI events
                key = cv2.waitKey(100) # 100ms wait
                if key == ord('q'):
                    system_running.clear() # Allow 'q' to stop too

            else:
                # --- IDLE STATE ---
                
                # Check if we just stopped
                if last_state:
                    # Just transitioned to OFF
                    if lcd:
                        lcd.clear()
                        lcd.setCursor(0,0); lcd.print("Hello! To start")
                        lcd.setCursor(0,1); lcd.print("press ---->")
                        lcd.setRGB(255, 255, 255)
                    
                    led_ctrl.stop()
                    if servo_ctrl: servo_ctrl.stop()
                    
                    cv2.destroyAllWindows()
                    # Also need cv2.waitKey(1) to process the destroy event on some systems
                    cv2.waitKey(1)
                    
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
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
