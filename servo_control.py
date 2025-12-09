
import time
from adafruit_servokit import ServoKit

# Initialize the PCA9685 using the default address (0x40).
kit = ServoKit(channels=16)

def move_smoothly(servo, start_angle, end_angle, duration):
    """
    Moves a servo smoothly from start_angle to end_angle over a specified duration.
    
    :param servo: The servo object (e.g., kit.servo[0])
    :param start_angle: The starting angle (0-180)
    :param end_angle: The target angle (0-180)
    :param duration: Time in seconds to complete the movement
    """
    # Frequency of updates (Hz) - how many times per second we update the position
    update_frequency = 50 
    
    # Total number of steps
    steps = int(duration * update_frequency)
    
    # Time to sleep between each step
    delay = 1.0 / update_frequency
    
    # Calculate the change in angle for each step
    angle_step = (end_angle - start_angle) / steps
    
    current_angle = start_angle
    
    for _ in range(steps):
        current_angle += angle_step
        # Ensure we stay within bounds (optional, but good practice)
        if current_angle < 0: current_angle = 0
        if current_angle > 180: current_angle = 180
        
        servo.angle = current_angle
        time.sleep(delay)
        
    # Ensure it lands exactly on the target angle at the end
    servo.angle = end_angle

print("Initializing Smooth Servo Control...")
print("------------------------------------")

try:
    # Example usage:
    servo_channel = 0
    my_servo = kit.servo[servo_channel]
    
    # Reset to 0 first (fast)
    print("Resetting to 0 degrees (fast)...")
    my_servo.angle = 0
    time.sleep(1)
    
    while True:
        # Move from 0 to 180 degrees over 3 seconds
        print("Moving to 180 degrees smoothly (3 seconds)...")
        move_smoothly(my_servo, 0, 180, 3.0)
        time.sleep(1)
        
        # Move from 180 to 90 degrees over 2 seconds
        print("Moving to 90 degrees smoothly (2 seconds)...")
        move_smoothly(my_servo, 180, 90, 2.0)
        time.sleep(1)
        
        # Move from 90 to 0 degrees over 0.5 seconds (faster)
        print("Moving to 0 degrees smoothly (0.5 seconds)...")
        move_smoothly(my_servo, 90, 0, 0.5)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting")
    # Optional: Release
    # my_servo.angle = None 
