import time
from rgb1602 import RGB1602

def main():
    print("Attempting to connect to RGB LCD (0x3E/0x60)...")
    
    try:
        # Initialize
        lcd = RGB1602(16, 2)

        # Test Colors
        lcd.setRGB(0, 0, 0)
        lcd.setCursor(0, 0)
        lcd.print("Hello! Press to")
        lcd.setCursor(0, 1)
        lcd.print("start -->")
        time.sleep(4)

        lcd.setRGB(127, 127, 127)
        time.sleep(6)

        lcd.setRGB(255, 255, 255)
        time.sleep(4)
        


        lcd.clear()
        lcd.print("Done.")
        time.sleep(1)
        # lcd.close() # Optional: turn off

    except Exception as e:
        print(f"Error: {e}")
        print("Ensure 'smbus2' is installed: pip install smbus2")

if __name__ == "__main__":
    main()
