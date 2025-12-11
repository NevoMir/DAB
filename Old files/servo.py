import time
from adafruit_servokit import ServoKit

# Initialize the PCA9685 using the default address (0x40).
# channels=16 tells the library we are using the 16-channel board.
kit = ServoKit(channels=16)

print("Controlling Standard (Positional) Servo on Channel 0...")
print("---------------------------------------------------")

try:
    while True:
        # Move to 0 degrees
        print("Moving to 0 degrees")
        kit.servo[0].angle = 0
        time.sleep(2)
        
        # Move to 90 degrees
        print("Moving to 90 degrees")
        kit.servo[0].angle = 90
        time.sleep(2)

        # Move to 180 degrees
        print("Moving to 180 degrees")
        kit.servo[0].angle = 180
        time.sleep(2)

except KeyboardInterrupt:
    # Optional: Move to a safe position on exit, or just stop sending signals
    # kit.servo[0].angle = None # Release
    print("\nExiting")
