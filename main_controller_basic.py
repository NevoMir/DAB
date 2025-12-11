import time
from gpiozero import Button
from adafruit_servokit import ServoKit
from rgb1602 import RGB1602

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

def run_servo_logic(kit):
    print("Initializing Smooth Servo Control...")
    print("------------------------------------")
    
    try:
        servo_channel = 0
        my_servo = kit.servo[servo_channel]
        
        # Reset to 0 first (fast)
        print("Resetting to 0 degrees (fast)...")
        my_servo.angle = 0
        time.sleep(1)
        
        while True:
            # Move from 0 to 180 degrees over 3 seconds
            print("Moving to 180 degrees smoothly (3 seconds)...")
            move_smoothly(my_servo, 0, 180, 4.0)
            time.sleep(1)
            
            # Move from 180 to 90 degrees over 2 seconds
            print("Moving to 0 degrees smoothly (2 seconds)...")
            move_smoothly(my_servo, 180, 0, 5.0)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting Servo Logic")
        # Optional: Release
        # my_servo.angle = None 

def main():
    # 1. Initialize LCD
    print("Initializing LCD...")
    try:
        lcd = RGB1602(16, 2)
        lcd.setRGB(0, 0, 0) # Off initially or set a color? User didn't specify color, let's just make sure text is visible (Backlight usually needed). 
        # Actually in test_lcd.py they did lcd.setRGB(0,0,0) then printed text. 
        # Usually RGB1602 needs a backlight color to be readable. 
        # test_lcd.py does:
        # lcd.setRGB(0, 0, 0) -> this typically turns OFF the backlight or sets it to black.
        # But maybe for this specific model it initializes differently?
        # Let's set it to white (255, 255, 255) or just leave it if 0,0,0 works for them. 
        # Actually, looking at test_lcd.py:
        # lcd.setRGB(0, 0, 0)
        # lcd.print("Hello! Press to")
        # Then later it does setRGB(127, 127, 127) etc.
        # I will start with a visible color to be safe, e.g. White, or just follow their pattern if they think it works.
        # Their test_lcd.py implies they might strictly want what's there. 
        # However, "0,0,0" usually means off. I'll stick to a standard White (255,255,255) for visibility unless they requested specific.
        # Re-reading test_lcd.py:
        # lcd.setRGB(0, 0, 0) -> Print... -> Sleep 4 -> setRGB(127...)
        # I'll stick to a safe default of White (255, 255, 255) for the message so they can read it.
        lcd.setRGB(255, 255, 255) 
        
        lcd.setCursor(0, 0)
        lcd.print("Hello! To start")
        lcd.setCursor(0, 1)
        lcd.print("press ---->")
    except Exception as e:
        print(f"LCD Initialization failed: {e}")
        return

    # 2. Initialize Button
    print("Initializing Button...")
    try:
        # Connected to GPIO 4, Active High (pull_up=False) based on button_gpiozero.py
        button = Button(4, pull_up=False)
    except Exception as e:
        print(f"Button Initialization failed: {e}")
        return

    # 3. Initialize Servo Kit
    print("Initializing Servo Kit...")
    try:
        kit = ServoKit(channels=16)
    except Exception as e:
        print(f"Servo Kit Initialization failed: {e}")
        return

    # 4. Wait for Button Press
    print("Waiting for button press...")
    button.wait_for_press()
    print("Button pressed! Starting servo control...")

    # 5. Update LCD and Run Servo
    try:
        lcd.clear()
        lcd.setCursor(0, 0)
        lcd.print("Running...")
        # Optional: Green background for running
        lcd.setRGB(0, 255, 0) 
    except:
        pass # Ignore LCD errors during run if any

    run_servo_logic(kit)

if __name__ == "__main__":
    main()
