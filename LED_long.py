import board
import neopixel
import time

pixel_pin = board.D12      # GPIO12 (pin physique 32)
num_pixels = 30            # peu importe, 10 suffit pour tester

pixels = neopixel.NeoPixel(
    pixel_pin,
    num_pixels,
    brightness=0.3,
    auto_write=True,
    pixel_order=neopixel.GRB
)

while True:
    pixels[0] = (255, 0, 0)   # première LED en rouge
    time.sleep(1)
    pixels[0] = (0, 0, 0)     # éteinte
    time.sleep(1)

