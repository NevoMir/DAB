from adafruit_servokit import ServoKit
import time

def release_servo():
    try:
        print("Initializing ServoKit...")
        kit = ServoKit(channels=16)
        
        print("Releasing Servo 0...")
        # Setting angle to None stops the PWM signal, releasing the holding torque
        kit.servo[0].angle = None
        
        print("Servo released. You should be able to move it freely now.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    release_servo()
