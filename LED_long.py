import board
import neopixel
import time

# -----------------------------
# Configuration
# -----------------------------
pixel_pin = board.D12      # GPIO 12 pour la LED band
num_pixels = 60            # Mets ici le nombre de LEDs de ta bande
ORDER = neopixel.GRB       # SK6812 RGB (sans blanc)

pixels = neopixel.NeoPixel(
    pixel_pin,
    num_pixels,
    brightness=0.3,
    auto_write=False,
    pixel_order=ORDER
)

# -----------------------------
# Boucle principale
# -----------------------------
while True:
    # Rouge
    pixels.fill((255, 0, 0))
    pixels.show()
    time.sleep(1)

    # Vert
    pixels.fill((0, 255, 0))
    pixels.show()
    time.sleep(1)

    # Bleu
    pixels.fill((0, 0, 255))
    pixels.show()
    time.sleep(1)
