import time
from RPLCD.i2c import CharLCD

# Common I2C addresses for LCDs are 0x27 or 0x3F
# Run 'i2cdetect -y 1' on your Pi to confirm
I2C_ADDR = 0x27 

def main():
    print(f"Attempting to connect to LCD at {hex(I2C_ADDR)}...")
    
    try:
        # Initialize the LCD
        # port=1 corresponds to /dev/i2c-1 (Standard on Pi)
        lcd = CharLCD(i2c_expander='PCF8574', address=I2C_ADDR, port=1,
                      cols=16, rows=2, dotsize=8,
                      charmap='A00',
                      auto_linebreaks=True,
                      backlight_enabled=True)
        
        print("Success! Writing to display...")
        
        # Step 1: Basic String
        lcd.clear()
        lcd.write_string('Hello, World!')
        lcd.crlf() # Carriage return + Line feed
        lcd.write_string('It works!')
        time.sleep(3)
        
        # Step 2: Backlight Blink
        print("Blinking backlight...")
        for _ in range(3):
            lcd.backlight_enabled = False
            time.sleep(0.5)
            lcd.backlight_enabled = True
            time.sleep(0.5)
            
        # Step 3: Clear and cleanup
        lcd.clear()
        lcd.write_string('Test Complete')
        time.sleep(2)
        lcd.clear()
        # lcd.close(clear=True) # Optional closing
        print("Test Complete.")
        
    except OSError as e:
        print(f"Error: Could not connect to LCD at {hex(I2C_ADDR)}.")
        print("1. Check wiring (SDA to Pin 3, SCL to Pin 5, VCC to 5V, GND to GND)")
        print("2. Check address with 'i2cdetect -y 1'")
        print(f"3. System Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
