import time
from rgb1602 import RGB1602

def main():
    print("Attempting to connect to RGB LCD (0x3E/0x60)...")
    
    try:
        # Initialize
        lcd = RGB1602(16, 2)

        # Test Colors
        lcd.setCursor(0, 0)
        lcd.print("Hello! Start by")
        lcd.setCursor(0, 1)
        lcd.print("pressing the button")
        time.sleep(3)
        
        lcd.setRGB(255, 0, 0)
        time.sleep(1)
        
        lcd.setRGB(0, 255, 0)
        lcd.setCursor(0, 1) # Move to start
        lcd.print("Color: GREEN") 
        time.sleep(1)
        
        lcd.setRGB(127, 0, 255)
        lcd.setCursor(0, 0)
        lcd.print("Color: VIOLET ")
        time.sleep(1)
        
        # Test Text
        print("Testing Text...")
        lcd.setRGB(255, 255, 255) # White
        lcd.clear()
        
        lcd.setCursor(0, 0)
        lcd.print("Hello Nevo!")
        
        lcd.setCursor(0, 1) # Second line
        lcd.print("It Works! :)")
        
        time.sleep(3)
        
        lcd.clear()
        lcd.print("Done.")
        time.sleep(1)
        # lcd.close() # Optional: turn off

    except Exception as e:
        print(f"Error: {e}")
        print("Ensure 'smbus2' is installed: pip install smbus2")

if __name__ == "__main__":
    main()
