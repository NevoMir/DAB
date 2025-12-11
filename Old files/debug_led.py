import board
import neopixel
import time

# Configuration
# user used D12 in LED_long.py
PIN = board.D18
NUM_PIXELS = 30 # Start with 30, can increase if strip is longer
ORDER = neopixel.GRB # Try GRBW if GRB produces wrong colors

print(f"Initializing NeoPixel strip on {PIN} with {NUM_PIXELS} pixels.")

try:
    pixels = neopixel.NeoPixel(
        PIN,
        NUM_PIXELS,
        brightness=0.2, # Low brightness to save power/eyes
        auto_write=False,
        pixel_order=ORDER
    )

    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 255),# White (RGB mixed)
        (0, 0, 0)       # Off
    ]

    color_names = ["Red", "Green", "Blue", "White", "Off"]

    while True:
        for color, name in zip(colors, color_names):
            print(f"Displaying {name}")
            pixels.fill(color)
            pixels.show()
            time.sleep(1)

except Exception as e:
    print(f"An error occurred: {e}")
except KeyboardInterrupt:
    print("Exiting...")
    pixels.fill((0, 0, 0))
    pixels.show()
