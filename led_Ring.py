import board
import neopixel
import time

# Configuration
pixel_pin = board.D18  # This is GPIO 18
num_pixels = 5       # Change this to the number of LEDs on your ring
ORDER = neopixel.GRB   # Most rings use Green-Red-Blue ordering

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

while True:
    # Make them Red
    pixels.fill((255, 0, 0))
    pixels.show()
    time.sleep(1)

    # Make them Green
    pixels.fill((0, 255, 0))
    pixels.show()
    time.sleep(1)

    # Make them Blue
    pixels.fill((0, 0, 255))
    pixels.show()
    time.sleep(1)

    # Make them White
    pixels.fill((255, 255, 255))
    pixels.show()
    time.sleep(1)