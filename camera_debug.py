import time
import os
import subprocess
import sys
import cv2
import numpy as np

def run_command(command):
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Error/Log:")
            print(result.stderr)
        return result.returncode
    except Exception as e:
        print(f"Failed to run command: {e}")
        return -1

def test_camera(camera_num):
    print(f"\n----------------------------------------")
    print(f"Testing Camera {camera_num}...")
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2(camera_num=camera_num)
        
        # Configure for a simple capture
        print("Configuring camera...")
        config = picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
        picam2.configure(config)
        
        print("Starting camera...")
        picam2.start()
        
        # Wait for auto-exposure/white-balance
        print("Waiting 2 seconds for warm-up...")
        time.sleep(2)
        
        print("Capturing image...")
        image = picam2.capture_array()
        picam2.stop()
        picam2.close()
        
        if image is not None:
            filename = f"debug_capture_cam{camera_num}.jpg"
            # Convert XRGB/RGBA to BGR for OpenCV
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
            cv2.imwrite(filename, image)
            print(f"SUCCESS! Image saved to {filename}")
            print(f"Image shape: {image.shape}")
            print(f"Mean pixel value: {np.mean(image)}")
            if np.mean(image) < 5:
                print("WARNING: Image is very dark (almost black). Check if lens cap is on.")
            return True
        else:
            print("FAILURE: Captured image is None")
            return False
            
    except ImportError:
        print("Error: picamera2 library not found.")
        return False
    except Exception as e:
        print(f"FAILURE: Exception while testing Camera {camera_num}: {e}")
        return False

if __name__ == "__main__":
    print("=== Camera Debug Tool ===")
    print("This script will check for available cameras and try to capture a single image from each.")
    
    # Check libcamera-hello list
    print("\n[Step 1] Checking available cameras with libcamera-hello:")
    run_command("rpicam-hello --list-cameras")
    
    # Test Python capture for both potential slots
    print("\n[Step 2] Testing Python Access")
    test_camera(0)
    test_camera(1)
    
    print("\n=== Debug Complete ===")
    print("If you see 'SUCCESS' above, the camera hardware is working.")
    print("Check the generated .jpg files to verify the image quality.")
