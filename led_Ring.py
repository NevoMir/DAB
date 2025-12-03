import board
import neopixel
import time

# # Configuration
# pixel_pin = board.D18  # This is GPIO 18
# num_pixels = 5       # Change this to the number of LEDs on your ring
# ORDER = neopixel.GRB   # Most rings use Green-Red-Blue ordering

# pixels = neopixel.NeoPixel(
#     pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
# )

pixels = neopixel.NeoPixel(board.D18, 60, auto_write=False)

for i in range(60):
    pixels.fill((0, 0, 0))
    pixels[i] = (255, 0, 0)
    pixels.show()
    time.sleep(0.1)
