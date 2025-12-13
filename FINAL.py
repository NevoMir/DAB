import time
import threading
import cv2
import socket
import board
import neopixel
import os
import sys
import random
import datetime
import subprocess
from flask import Flask, Response, render_template_string
from gpiozero import Button
from adafruit_servokit import ServoKit
from rgb1602 import RGB1602

# Import CSI Camera Class
try:
    from CSI_camera import CameraStream as CSICameraStream
except ImportError:
    print("Error: Could not import CameraStream (CSI)")

# ==============================================================================
# GIT INTEGRATION
# ==============================================================================
def git_push_changes():
    """
    Adds, commits, and pushes changes in the 'Color' folder to the remote repository.
    """
    try:
        print("  [Git] Starting sync...")
        # Add changes in Color folder (Root of repo)
        subprocess.run(["git", "add", "Color/"], check=True)
        
        # Commit (will fail if nothing to commit, so check=False is safer)
        subprocess.run(["git", "commit", "-m", "Auto-save Color images"], check=False)
        
        # Push
        subprocess.run(["git", "push"], check=True)
        print("  [Git] Pushed images to remote successfully.")
    except Exception as e:
        print(f"  [Git] Error during sync: {e}")

# REDEFINE USB CAMERA CLASS LOCALLY (Robust Version)
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
            return False

    def _update(self):
        while self.running and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame
                    self.error_count = 0
                else:
                    self.error_count += 1
                    if self.error_count % 100 == 1:
                         # Suppress spam
                         pass
                    time.sleep(0.1)
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
led_update_event = threading.Event() # Signal to change LEDs

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
        <head><title>DAB Stream</title></head>
        <body style="background:#222;color:#fff;text-align:center;">
            <h1>Live Feeds</h1>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:20px;">
                {% for key in active_keys %}
                <div style="background:#333;padding:10px;">
                    <h3>{{ key }}</h3>
                    <img src="{{ url_for('video_feed', cam_key=key) }}" style="max-width:400px;">
                </div>
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
# LED CONTROLLER (Seed Logic)
# ==============================================================================
class LEDController:
    def __init__(self):
        self.running = False
        self.thread = None
        self.pixels_1 = neopixel.NeoPixel(LED_PIN_1, LED_COUNT_1, brightness=0.4, auto_write=False)
        self.pixels_2 = neopixel.NeoPixel(LED_PIN_2, LED_COUNT_2, brightness=1.0, auto_write=False)

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def _animate(self):
        # Initial Light Up
        self._set_seeds()
        
        while self.running:
            # Wait for signal OR just update
            if led_update_event.wait(timeout=0.1):
                self._set_seeds()
                led_update_event.clear()
            
            if not self.running: break

    def _set_seeds(self):
        # STRIP: 1 to 3 seeds
        # Max Brightness 0.35 to keep current under limit (120*0.06*0.35 = 2.52A)
        self._apply_seed_logic(self.pixels_1, LED_COUNT_1, random.randint(1, 3), max_brightness=0.35)
        # RING: 2 seeds
        # Max Brightness 0.8 (32*0.04*0.8 = 1.02A)
        self._apply_seed_logic(self.pixels_2, LED_COUNT_2, 2, max_brightness=0.8)

    def _apply_seed_logic(self, pixels, num_leds, num_seeds, max_brightness=1.0):
        pixels.fill((0, 0, 0)) # Clear
        
        # Avoid division by zero
        if num_seeds < 1: num_seeds = 1
        max_lit = num_leds // num_seeds 
        if max_lit < 1: max_lit = 1

        for _ in range(num_seeds):
            # 1. Random Seed Position
            pos = random.randint(0, num_leds - 1)
            
            # 2. Random number of LEDs to light up (1 to max_lit)
            lit_count = random.randint(1, max_lit)
            
            # 3. Random Color (Yellow to White) & Brightness
            # Scaled to safety limit
            safe_b = random.uniform(0.1, max_brightness)
            pixels.brightness = safe_b 
            
            # Colors: Yellow(255,255,0) -> White(255,255,255)
            # R=255, G=255, B=0-255
            blue_val = random.randint(0, 255)
            
            color = (255, 255, blue_val)

            # 4. Light up neighbors to the right
            for i in range(lit_count):
                idx = pos + i
                if idx < num_leds:
                    pixels[idx] = color
        
        pixels.show()

    def stop(self):
        self.running = False
        led_update_event.set() 
        if self.thread: 
            self.thread.join()
            self.thread = None
        try:
            self.pixels_1.fill((0,0,0)); self.pixels_1.show()
            self.pixels_2.fill((0,0,0)); self.pixels_2.show()
        except: pass

# ==============================================================================
# SNAPSHOT LOGIC
# ==============================================================================
def save_snapshots(counter):
    # Save to 'Color' folder in Repo Root
    base_path = 'Color'
    
    if not os.path.exists(base_path):
        try: os.makedirs(base_path)
        except: pass
        
    print(f"  [Snap] Saving images to {base_path}...")
    
    for name, cam in active_cameras.items():
        frame = cam.get_frame()
        if frame is not None:
            filename = ""
            h, w = frame.shape[:2]
            
            # ------------------------------------------------------------------
            # CROPPING LOGIC
            # ------------------------------------------------------------------
            if "USB" in name:
                # Crop Upper 30%, Left 15%, Right 15%
                # Result: y[0.3h : h], x[0.15w : 0.85w]
                y_start = int(0.3 * h)
                x_start = int(0.15 * w)
                x_end = int(0.85 * w)
                frame = frame[y_start:h, x_start:x_end]
                
                idx = name.split()[-1]
                filename = f"USB{idx}_{counter}.jpg"
                
            elif "CSI" in name:
                idx = name.split()[-1]
                
                if idx == "1": # Specific Request for CSI 1
                    # Crop Lower 30%, Left 10%, Right 10%
                    # Result: y[0 : 0.7h], x[0.1w : 0.9w]
                    y_end = int(0.7 * h)
                    x_start = int(0.1 * w)
                    x_end = int(0.9 * w)
                    frame = frame[0:y_end, x_start:x_end]
                    filename = f"CSI45_{counter}.jpg"
                    
                elif idx == "0": 
                    # No Crop for CSI 0
                    filename = f"CSI90_{counter}.jpg"
                else: 
                    filename = f"CSI_Unknown_{counter}.jpg"
            
            # Save
            if filename:
                full_path = os.path.join(base_path, filename)
                try:
                    cv2.imwrite(full_path, frame)
                except Exception as e:
                    print(f"    Failed to save {filename}: {e}")

# ==============================================================================
# SERVO CONTROLLER (10-Step Random)
# ==============================================================================
class ServoController:
    def __init__(self, kit):
        self.kit = kit
        self.running = False
        self.stop_requested = False
        self.thread = None
        
    def request_stop(self):
        """Signals the controller to stop after the current step completes."""
        self.stop_requested = True
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_sequence, daemon=True)
        self.thread.start()

    def _run_sequence(self):
        servo = self.kit.servo[0]
        SPEED = 180.0 / 5.0 # deg/sec
        
        # Init: Go to 0 slowly
        self._move_to(servo, 0, SPEED)
        
        current_angle = 0.0
        direction = 1 # 1=Up, -1=Down
        
        # 10 Steps
        for i in range(1, 11):
            if not self.running: break
            if self.stop_requested: break # Stop before starting new step
            
            # TRIGGER LED CHANGE START OF MOVE
            led_update_event.set()
            
            # Calculate next step
            step = random.randint(3, 30)
            
            # Bounce Logic
            next_angle = current_angle + (step * direction)
            if next_angle > 180:
                diff = next_angle - 180
                next_angle = 180 - diff # Simple reflection? 
                direction = -1
                # Or user simple logic: Re-calc
                if current_angle > 150: direction = -1
                next_angle = current_angle - step if direction == -1 else current_angle + step
                
            elif next_angle < 0:
                direction = 1
                next_angle = current_angle + step
                
            # Clamp just in case
            if next_angle > 180: next_angle = 180
            if next_angle < 0: next_angle = 0
            
            print(f"  [Servo] Step {i}/10: Moving {current_angle:.1f} -> {next_angle:.1f}")
            self._move_to(servo, next_angle, SPEED)
            current_angle = next_angle
            
            # STOPPED
            if not self.running: break
            if self.stop_requested: break # Stop after move
            
            time.sleep(1.5)
            
            if not self.running: break
            if self.stop_requested: break # Stop after sleep
            
            if not self.running: break
            save_snapshots(i)
            
            if not self.running: break
            time.sleep(0.5)
        
        # End of sequence
        # Only return to 0 if we finished normally (NOT stopped early)
        if self.running and not self.stop_requested:
            print("  [Servo] Sequence Done. Returning to 0.")
            self._move_to(servo, 0, SPEED)
            
            # Git Push happens in Main loop after thread join, 
            # OR we can do it here. 
            # To avoid threading conflicts, let's signal Main loop via a flag or just do it here.
            # Doing it here blocks the thread, which is fine.
            if self.running:
                git_push_changes()
        
        self.running = False # Mark as done

    def _move_to(self, servo, target, speed):
        start = servo.angle
        if start is None: start = 0
        dist = abs(target - start)
        duration = dist / speed
        steps = int(duration * 50) 
        if steps < 1: steps = 1
        
        delta = (target - start) / steps
        curr = start
        
        for _ in range(steps):
            if not self.running: return
            curr += delta
            if curr < 0: curr = 0
            if curr > 180: curr = 180
            servo.angle = curr
            time.sleep(0.02)
        servo.angle = target

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None
    
    def is_alive(self):
        return self.thread and self.thread.is_alive()

# ==============================================================================
# MAIN LOGIC
# ==============================================================================
def get_all_ips():
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ips = result.stdout.strip().split()
        return [ip for ip in ips if ip]
    except: return []

def main():
    lcd = None
    try:
        lcd = RGB1602(16, 2)
    except: print("LCD Init Failed")

    button = Button(BUTTON_PIN, pull_up=False)

    kit = None
    try: kit = ServoKit(channels=16)
    except: print("ServoKit Init Failed")

    led_ctrl = LEDController()
    servo_ctrl = ServoController(kit) if kit else None

    # Start Cameras
    for i in range(2):
        try:
            cam = CSICameraStream(i)
            if cam.start(): active_cameras[f"CSI Camera {i}"] = cam
        except: pass
    for i in range(10): 
        try:
            cam = USBCameraStream(i)
            if cam.start():
                print(f"  -> USB Camera {i} is VALID.")
                active_cameras[f"USB Camera {i}"] = cam
        except: pass

    # Flask
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()

    # Images
    images = []
    if os.path.exists(IMAGE_FOLDER):
        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        images = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(exts)]
        random.shuffle(images)

    if "DISPLAY" not in os.environ: os.environ["DISPLAY"] = ":0"
    window_name = "Slideshow"

    # Network Debug
    ips = get_all_ips()
    print("\n" + "="*40); print("       NETWORK DIAGNOSTICS"); print("="*40)
    for i, ip in enumerate(ips): print(f"  {i+1}. http://{ip}:5000")
    print("="*40 + "\n")

    try:
        # ==========================================
        # PHASE 1: START SCREEN
        # ==========================================
        print("PHASE 1: Waiting for Button...")
        
        # LCD: White (200, 200, 200)
        # "Hello! Press to // start ----->"
        if lcd:
            lcd.setRGB(200, 200, 200)
            lcd.clear()
            lcd.setCursor(0,0); lcd.print("Hello! Press to")
            lcd.setCursor(0,1); lcd.print("start ----->")
        
        # Show Start.jpeg
        start_img_path = os.path.join(IMAGE_FOLDER, "Start.jpeg")
        if os.path.exists(start_img_path):
            img = cv2.imread(start_img_path)
            if img is not None:
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.imshow(window_name, img)
                cv2.waitKey(10)
        
        # Wait for button
        button.wait_for_press()
        print("Button Pressed! Starting...")

        # ==========================================
        # PHASE 2: RUNNING
        # ==========================================
        # LCD: Orange (255, 165, 0) "Running..."
        if lcd:
            lcd.setRGB(255, 165, 0)
            lcd.clear()
            lcd.setCursor(0,0); lcd.print("Running...")
        
        led_ctrl.start()
        if servo_ctrl: 
            servo_ctrl.start()
            # Feature: Stop on Button Press during Phase 2
            # Use 'when_pressed' callback which runs in a thread.
            # It signals the servo controller to stop gracefully.
            button.when_pressed = lambda: servo_ctrl.request_stop()
        
        # Slideshow Loop (Blocking Main Thread while Servo runs)
        current_img_idx = 0
        last_slide_time = 0
        SLIDE_DURATION = 3.0
        
        while True:
            # Check if servo finished
            # Check if servo finished
            if servo_ctrl and not servo_ctrl.running:
                # Sequence done
                break
            
            # Also break if stop requested (redundant but safe)
            if servo_ctrl and servo_ctrl.stop_requested:
                break
                
            # Slideshow
            now = time.time()
            if images and (now - last_slide_time > SLIDE_DURATION):
                img = cv2.imread(images[current_img_idx])
                if img is not None:
                    try:
                        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                        cv2.imshow(window_name, img)
                    except: pass
                current_img_idx = (current_img_idx + 1) % len(images)
                last_slide_time = now
            
            if cv2.waitKey(50) == ord('q'): break

        # ==========================================
        # PHASE 3: FINISH & EXIT
        # ==========================================
        print("Sequence Finished. Shutting down...")
        
        # 1. IMMEDIATE UI UPDATE (Prioritize this before any crash risk)
        if lcd:
            try:
                lcd.setRGB(0, 255, 0) # Green
                lcd.clear()
                lcd.setCursor(0,0); lcd.print("Thank you and")
                lcd.setCursor(0,1); lcd.print("good bye")
            except: pass

        # 2. Turn off lights (Gentle stop)
        try:
            led_ctrl.stop()
        except: pass

        # 3. Show Finished.jpeg
        fin_img_path = os.path.join(IMAGE_FOLDER, "Finished.jpeg")
        if os.path.exists(fin_img_path):
            try:
                img = cv2.imread(fin_img_path)
                if img is not None:
                    try:
                        cv2.imshow(window_name, img)
                        cv2.waitKey(10)
                    except: pass
            except: pass
        
        # Wait 5 seconds to let user see "Finished" and Git to complete if lagging
        time.sleep(5)

        time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n[User] Ctrl+C Caught. Exiting...")

    except Exception as e:
        print(f"ERROR: {e}")
        # LCD: Red (255, 0, 0) "Something is // wrong"
        if lcd:
            try:
                lcd.setRGB(255, 0, 0)
                lcd.clear()
                lcd.setCursor(0,0); lcd.print("Something is")
                lcd.setCursor(0,1); lcd.print("wrong")
            except: pass
        time.sleep(10)

    finally:
        # CLEANUP (Legacy cleanup if not done above)
        print("Final Cleanup...")
        try: led_ctrl.stop()
        except: pass
        
        # ----------------------------------------------------
        # FORCE LEDS OFF (Robust Method)
        # ----------------------------------------------------
        try:
            print("  -> Forcing LEDs OFF...")
            # Re-init simply to flush buffer
            p1 = neopixel.NeoPixel(LED_PIN_1, LED_COUNT_1, auto_write=False)
            p1.fill((0,0,0)); p1.show()
            
            p2 = neopixel.NeoPixel(LED_PIN_2, LED_COUNT_2, auto_write=False)
            p2.fill((0,0,0)); p2.show()
        except Exception as e:
            print(f"  -> LED Force Off Failed: {e}")
        # ----------------------------------------------------
        
        if servo_ctrl: 
            try: servo_ctrl.stop()
            except: pass
        
        # Stop Cameras
        for cam in active_cameras.values(): 
            try: cam.stop()
            except: pass
        
        # Close Window
        try:
            cv2.destroyAllWindows()
            for _ in range(5): cv2.waitKey(1)
        except: pass
        
        # LCD Off (Optional, user might want "Good bye" to stay? 
        # User said "Show... good bye", usually implies persistent until power off or restart.
        # But script exits. If script exits, LCD state might persist or clear. 
        # Let's LEAVE it asking "Thank you" (Green) and not clear it to black.
        # Only clear if error? No, let's leave it Green.
        
        print("Exited.")
        sys.exit(0)

if __name__ == "__main__":
    main()
