import time
from adafruit_servokit import ServoKit

# Initialize the PCA9685 using the default address (0x40).
kit = ServoKit(channels=16)

print("Controlling TD-8120MG 360deg Servo on Channel 0...")
print("---------------------------------------------------")
print("IMPORTANT: The behavior you described (0=fast, 90=stop, 180=reverse) confirms")
print("that this is a 'Continuous Rotation' servo. It cannot move to a specific angle.")
print("It can only control Speed and Direction.")
print("---------------------------------------------------")

try:
    while True:
        # Full Speed Forward
        # Equivalent to '0 degrees' on a continuous servo (pulse ~1000us)
        print("Full Speed Forward (Throttle 1.0)")
        kit.continuous_servo[0].throttle = 1.0
        time.sleep(3)
        
        # Stop
        # Equivalent to '90 degrees' on a continuous servo (pulse ~1500us)
        print("Stop (Throttle 0.0)")
        kit.continuous_servo[0].throttle = 0.0
        time.sleep(2)

        # Full Speed Reverse
        # Equivalent to '180 degrees' on a continuous servo (pulse ~2000us)
        print("Full Speed Reverse (Throttle -1.0)")
        kit.continuous_servo[0].throttle = -1.0
        time.sleep(3)

        # Stop again
        print("Stop (Throttle 0.0)")
        kit.continuous_servo[0].throttle = 0.0
        time.sleep(2)
        
        # Variable Speed Example
        print("Slow Forward (Throttle 0.5)")
        kit.continuous_servo[0].throttle = 0.5
        time.sleep(2)
        
        print("Stop")
        kit.continuous_servo[0].throttle = 0.0
        time.sleep(1)

except KeyboardInterrupt:
    # Stop the servo on exit
    kit.continuous_servo[0].throttle = 0.0
    print("\nExiting")