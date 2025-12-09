import time
import sys

# Try to import smbus, support both smbus and smbus2
try:
    import smbus2 as smbus
except ImportError:
    try:
        import smbus
    except ImportError:
        print("Error: smbus or smbus2 not found. Please run 'pip install smbus2'")
        sys.exit(1)

# Device I2C Addresses
LCD_ADDRESS = 0x3e
RGB_ADDRESS = 0x60

class RGB1602:
    def __init__(self, col, row, i2c_bus=1):
        self._col = col
        self._row = row
        self._bus = smbus.SMBus(i2c_bus)

        # Initialization sequence for AiP31068L
        try:
            time.sleep(0.050)
            self.command(0x28) # Function set: DL=0 (4-bit?), N=1 (2 lines), F=0 (5x8) - Note: Datasheet says 0x28 for 8-bit connection usually, let's follow Waveshare init
            time.sleep(0.001)
            self.command(0x28)
            time.sleep(0.001)
            self.command(0x28)
            time.sleep(0.001)
            
            self.command(0x0C) # Display On, Cursor Off, Blink Off
            self.command(0x01) # Clear Display
            time.sleep(0.002)
            self.command(0x06) # Entry Mode: Increment, No Shift
            
            # Initialize RGB
            self.setReg(0x00, 0x00)
            self.setReg(0x01, 0x05)
            self.setReg(0x08, 0xAA) # LED control
            self.setRGB(255, 255, 255) # White backlight by default
            
        except Exception as e:
            print(f"Error initializing RGB1602: {e}")
            raise

    def command(self, cmd):
        self._bus.write_byte_data(LCD_ADDRESS, 0x80, cmd)

    def write(self, data):
        self._bus.write_byte_data(LCD_ADDRESS, 0x40, data)

    def setReg(self, reg, data):
        self._bus.write_byte_data(RGB_ADDRESS, reg, data)

    def setRGB(self, r, g, b):
        self.setReg(0x04, r)
        self.setReg(0x03, g)
        self.setReg(0x02, b)

    def setCursor(self, col, row):
        if row == 0:
            col |= 0x80
        else:
            col |= 0xC0
        self.command(col)

    def clear(self):
        self.command(0x01)
        time.sleep(0.002)

    def print(self, string):
        # Handle string input
        for char in str(string):
            self.write(ord(char))

    def close(self):
        self.clear()
        self.setRGB(0, 0, 0) # Turn off backlight
