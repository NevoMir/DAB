import time
from adafruit_servokit import ServoKit

# Initialize the PCA9685 using the default address (0x40).
# 'channels=16' tells the library we are using the 16-channel board.
kit = ServoKit(channels=16)

print("Moving Servo on Channel 0...")

# The TD-8120MG usually has a range of 180 degrees.
# Sometimes you need to adjust the pulse width range for specific servos,
# but the defaults (1000-2000us) usually work for a basic test.

try:
    while True:
        # Move to 0 degrees
        print("0 degrees")
        kit.servo[0].angle = 0
        time.sleep(3)
        
        # Move to 90 degrees
        print("90 degrees")
        kit.servo[0].angle = 90
        time.sleep(3)

        # Move to 180 degrees
        print("359 degrees")
        kit.servo[0].angle = 359
        time.sleep(3)

except KeyboardInterrupt:
    # Turn off the servo signal on exit to stop jitter
    kit.servo[0].angle = None
    print("\nExiting")