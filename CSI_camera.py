import time
import threading
import cv2
import numpy as np
try:
    from picamera2 import Picamera2
except ImportError:
    print("Error: picamera2 library not found. Please install it using the setup instructions.")
    exit(1)

class CameraStream:
    def __init__(self, camera_num, window_name):
        self.camera_num = camera_num
        self.window_name = window_name
        self.picam2 = None
        self.running = False
        self.thread = None
        self.frame = None

    def start(self):
        try:
            print(f"Initializing Camera {self.camera_num}...")
            self.picam2 = Picamera2(camera_num=self.camera_num)
            
            # Configure camera for video capture
            # Using a lower resolution for smoother streaming of multiple cameras
            config = self.picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
            self.picam2.configure(config)
            self.picam2.start()
            
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            print(f"Camera {self.camera_num} started.")
            return True
        except IndexError:
            print(f"Failed to start Camera {self.camera_num}: Camera not found (IndexError). Check connection.")
            self.picam2 = None
            return False
        except Exception as e:
            print(f"Failed to start Camera {self.camera_num}: {e}")
            self.picam2 = None
            return False

    def _update(self):
        while self.running:
            try:
                # capture_array returns the image as a numpy array
                # wait=True ensures we wait for a new frame
                image = self.picam2.capture_array()
                
                # Picamera2 returns RGB (or XRGB), OpenCV expects BGR
                # If format is XRGB8888, we might need to drop the alpha channel and swap colors
                # XRGB usually comes as 4 bytes. 
                # Let's check shape. If it's (480, 640, 4), it's BGRA or RGBA.
                # Usually create_preview_configuration with XRGB8888 gives us something we can convert.
                
                if image is not None:
                    # Convert XRGB/RGBA to BGR for OpenCV
                    if image.shape[2] == 4:
                        self.frame = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
                    else:
                        self.frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                        
            except Exception as e:
                print(f"Error reading from Camera {self.camera_num}: {e}")
                time.sleep(0.1)

    def get_frame(self):
        return self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
            print(f"Camera {self.camera_num} stopped.")

def main():
    # Initialize cameras
    cam0 = CameraStream(0, "Camera 0")
    cam1 = CameraStream(1, "Camera 1")

    cam0_started = cam0.start()
    cam1_started = cam1.start()

    if not cam0_started and not cam1_started:
        print("No cameras could be started. Exiting.")
        return

    print("Press 'q' to quit.")

    try:
        while True:
            if cam0_started:
                frame0 = cam0.get_frame()
                if frame0 is not None:
                    cv2.imshow("Camera 0", frame0)

            if cam1_started:
                frame1 = cam1.get_frame()
                if frame1 is not None:
                    cv2.imshow("Camera 1", frame1)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if cam0_started:
            cam0.stop()
        if cam1_started:
            cam1.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
