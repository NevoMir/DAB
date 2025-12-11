import time
from rgb1602 import RGB1602
from gpiozero import Button

# Configuration
# Button GPIO Pin (BCM numbering)
BUTTON_PIN = 17 

# Initialize LCD
# using our custom driver
lcd = RGB1602(16, 2)

# Initialize Button
# pull_up=True means the button connects GPIO to GND
button = Button(BUTTON_PIN, pull_up=True) 

def main():
    print("LCD Button Program Started")
    print(f"Button on GPIO {BUTTON_PIN}")
    
    # Clear screen initially
    lcd.setRGB(0, 0, 255) # Blue background
    lcd.clear()
    lcd.setCursor(0, 0)
    lcd.print("Click to START")
    print("Displaying: 'Click to START'")
    
    try:
        while True:
            # Wait for button press
            if button.is_pressed:
                print("Button Pressed!")
                
                # Visual Feedback: Green
                lcd.setRGB(0, 255, 0)
                lcd.clear()
                lcd.print("Started!")
                
                # Debounce / wait a bit so we don't spam
                time.sleep(1)
                
                # Optional: Reset after some time
                time.sleep(2)
                
                # Reset to Waiting state (Blue)
                lcd.setRGB(0, 0, 255)
                lcd.clear()
                lcd.print("Click to START")
                print("Reset to: 'Click to START'")
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting")
        lcd.close()

if __name__ == "__main__":
    main()
