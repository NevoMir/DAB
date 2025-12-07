import time
from RPLCD.i2c import CharLCD
from gpiozero import Button

# Configuration
# I2C Address: Usually 0x27 or 0x3F. Check with 'i2cdetect -y 1'
I2C_ADDR = 0x27 
# Button GPIO Pin (BCM numbering)
BUTTON_PIN = 17 

# Initialize LCD
# cols=16, rows=2
lcd = CharLCD(i2c_expander='PCF8574', address=I2C_ADDR, port=1,
              cols=16, rows=2, dotsize=8,
              charmap='A00',
              auto_linebreaks=True,
              backlight_enabled=True)

# Initialize Button
# pull_up=True means the button connects GPIO to GND
button = Button(BUTTON_PIN, pull_up=True) 

def main():
    print("LCD Button Program Started")
    print(f"Button on GPIO {BUTTON_PIN}")
    print(f"LCD at I2C {hex(I2C_ADDR)}")
    
    # Clear screen initially
    lcd.clear()
    lcd.write_string("Click to START")
    print("Displaying: 'Click to START'")
    
    try:
        while True:
            # Wait for button press
            if button.is_pressed:
                print("Button Pressed!")
                lcd.clear()
                lcd.write_string("Started!")
                
                # Debounce / wait a bit so we don't spam
                time.sleep(1)
                
                # Optional: Reset after some time or do something else?
                # For now, just stay "Started!" or go back?
                # Let's go back after 2 seconds for demo purposes
                time.sleep(2)
                lcd.clear()
                lcd.write_string("Click to START")
                print("Reset to: 'Click to START'")
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nExiting")
        lcd.clear()
        lcd.backlight_enabled = False
        lcd.close()

if __name__ == "__main__":
    main()
