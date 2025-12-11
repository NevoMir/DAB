import time
import threading
import cv2
import socket
import board
import neopixel
from flask import Flask, Response, render_template_string
from gpiozero import Button
from adafruit_servokit import ServoKit
from rgb1602 import RGB1602

try:
    from picamera2 import Picamera2
except ImportError:
    print("Warning: picamera2 not found. CSI cameras will not work.")

# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================
LED_PIN_1 = board.D12
LED_COUNT_1 = 120
LED_PIN_2 = board.D18
LED_COUNT_2 = 32

BUTTON_PIN = 4

# ==============================================================================
# FLASK & CAMERA STREAMING CLASSES
# ==============================================================================
app = Flask(__name__)
active_cameras = {}

class USBCameraStream:
    def __init__(self, camera_index):
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.thread = None
        self.frame = None
        self.lock = threading.Lock()
        self.name = f"USB Camera {camera_index}"

    def start(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"{self.name} started.")
            return True
        except Exception as e:
            print(f"Error starting {self.name}: {e}")
            return False

    def _update(self):
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.5)

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()
        if self.cap: self.cap.release()

class CSICameraStream:
    def __init__(self, camera_num):
        self.camera_num = camera_num
        self.picam2 = None
        self.running = False
        self.thread = None
        self.frame = None
        self.lock = threading.Lock()
        self.name = f"CSI Camera {camera_num}"

    def start(self):
        try:
            self.picam2 = Picamera2(camera_num=self.camera_num)
            config = self.picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
            self.picam2.configure(config)
            self.picam2.start()
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"{self.name} started.")
            return True
        except Exception as e:
            print(f"Failed to start {self.name}: {e}")
            return False

    def _update(self):
        while self.running:
            try:
                image = self.picam2.capture_array()
                if image is not None:
                    # Picamera2 XRGB8888 is BGRA, OpenCV needs BGR
                    if image.shape[2] == 4:
                        frame = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                    else:
                        frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    with self.lock:
                        self.frame = frame
            except:
                time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()

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
        time.sleep(0.04) # ~25 FPS limit

@app.route('/')
def index():
    active_keys = list(active_cameras.keys())
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
                    <h3>{{ active_cameras[key].name }}</h3>
                    <img src="{{ url_for('video_feed', cam_key=key) }}">
                </div>
                {% else %}
                <p>No cameras active.</p>
                {% endfor %}
            </div>
        </body>
    </html>
    """
    return render_template_string(html, active_keys=active_keys, active_cameras=active_cameras)

@app.route('/video_feed/<cam_key>')
def video_feed(cam_key):
    return Response(generate_frames(cam_key),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ==============================================================================
# LED CONTROLLER CLASS
# ==============================================================================
class LEDController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.pixels_1 = neopixel.NeoPixel(LED_PIN_1, LED_COUNT_1, brightness=0.2, auto_write=False)
        self.pixels_2 = neopixel.NeoPixel(LED_PIN_2, LED_COUNT_2, brightness=0.2, auto_write=False)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def _animate(self):
        print("Starting LED Animation Loop...")
        while self.running:
            # Sequence 1
            self.pixels_1.fill((255, 0, 0)) # Red
            self.pixels_2.fill((0, 0, 255)) # Blue
            self.pixels_1.show()
            self.pixels_2.show()
            time.sleep(1)
            if not self.running: break

            # Sequence 2
            self.pixels_1.fill((0, 255, 0)) # Green
            self.pixels_2.fill((255, 0, 0)) # Red
            self.pixels_1.show()
            self.pixels_2.show()
            time.sleep(1)
            if not self.running: break

            # Sequence 3
            self.pixels_1.fill((0, 0, 255)) # Blue
            self.pixels_2.fill((0, 255, 0)) # Green
            self.pixels_1.show()
            self.pixels_2.show()
            time.sleep(1)
            if not self.running: break

            # Sequence 4
            self.pixels_1.fill((255, 255, 255)) # White
            self.pixels_2.fill((255, 255, 255))
            self.pixels_1.show()
            self.pixels_2.show()
            time.sleep(1)

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()
        self.pixels_1.fill((0,0,0))
        self.pixels_2.fill((0,0,0))
        self.pixels_1.show()
        self.pixels_2.show()

# ==============================================================================
# SERVO & MAIN LOGIC
# ==============================================================================
def move_smoothly(servo, start_angle, end_angle, duration):
    update_frequency = 50 
    steps = int(duration * update_frequency)
    delay = 1.0 / update_frequency
    angle_step = (end_angle - start_angle) / steps
    current_angle = start_angle
    
    for _ in range(steps):
        current_angle += angle_step
        if current_angle < 0: current_angle = 0
        if current_angle > 180: current_angle = 180
        servo.angle = current_angle
        time.sleep(delay)
    servo.angle = end_angle

def run_servo_loop(kit):
    print("Starting Servo Loop...")
    servo = kit.servo[0]
    servo.angle = 0
    time.sleep(1)

    try:
        while True:
            # 0 -> 180 (3s)
            move_smoothly(servo, 0, 180, 4.0)
            time.sleep(1)
            # 180 -> 0 (2s)
            move_smoothly(servo, 180, 0, 5.0)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    # 1. Init LCD
    try:
        lcd = RGB1602(16, 2)
        lcd.setRGB(255, 255, 255)
        lcd.setCursor(0, 0)
        lcd.print("Hello! To start")
        lcd.setCursor(0, 1)
        lcd.print("press ---->")
    except Exception as e:
        print(f"LCD Init Error: {e}")
        return

    # 2. Init Button
    try:
        button = Button(BUTTON_PIN, pull_up=False)
    except Exception as e:
        print(f"Button Init Error: {e}")
        return

    # 3. Init Servo Kit
    try:
        kit = ServoKit(channels=16)
    except Exception as e:
        print(f"ServoKit Init Error: {e}")
        return

    print("Waiting for button press...")
    button.wait_for_press()
    print("Button Pressed! Starting System...")

    # UPDATE LCD
    try:
        lcd.clear()
        lcd.setCursor(0, 0)
        lcd.print("Running...")
        lcd.setCursor(0, 1)
        lcd.print(get_ip_address()) # Show IP so user knows where to look
        lcd.setRGB(0, 255, 0)
    except: pass

    # START LEDS
    led_controller = LEDController()
    led_controller.start()

    # START CAMERAS (Scan USB 0-4, CSI 0-1)
    # USB
    for i in range(5): 
        cam = USBCameraStream(i)
        if cam.start():
            active_cameras[f"usb_{i}"] = cam
            # Give it a tiny bit of time to init
            time.sleep(0.5)
            # If start() returned True but cap failed to read, it might be a dud index (or CSI alias) regarding implementation
            # But our start() checks isOpened(), so usually safe.
    
    # CSI
    for i in range(2):
        if f"usb_{i}" in active_cameras: continue # Avoid conflict if indices overlap in system
        cam = CSICameraStream(i)
        if cam.start():
            active_cameras[f"csi_{i}"] = cam

    # START WEBSERVER
    # Run Flask in a separate thread so servo loop can run in main thread
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    print(f"\nWeb Server running at http://{get_ip_address()}:5000\n")

    # START SERVO LOOP (Blocking)
    try:
        run_servo_loop(kit)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Cleanup
        led_controller.stop()
        for cam in active_cameras.values():
            cam.stop()
        try:
            lcd.clear()
            lcd.setRGB(0,0,0)
        except: pass

if __name__ == "__main__":
    main()
