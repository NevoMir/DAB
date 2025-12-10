import board
import neopixel
import time

# Configuration for Strip 1 (GPIO 12)
PIN_1 = board.D12
NUM_PIXELS_1 = 120
ORDER_1 = neopixel.GRB

# Configuration for Strip 2 (GPIO 18)
PIN_2 = board.D18
NUM_PIXELS_2 = 32  # Adjust this number if needed
ORDER_2 = neopixel.GRB

# Initialize both strips
# auto_write=False is recommended for better timing control
pixels_1 = neopixel.NeoPixel(PIN_1, NUM_PIXELS_1, brightness=0.3, auto_write=False, pixel_order=ORDER_1)
pixels_2 = neopixel.NeoPixel(PIN_2, NUM_PIXELS_2, brightness=0.3, auto_write=False, pixel_order=ORDER_2)

print("Starting Dual LED Control...")

try:
    while True:
        # Animation: Strip 1 Red, Strip 2 Blue
        print("Strip 1: Red, Strip 2: Blue")
        pixels_1.fill((255, 0, 0))
        pixels_2.fill((0, 0, 255))
        pixels_1.show()
        pixels_2.show()
        time.sleep(1)

        # Animation: Strip 1 Green, Strip 2 Red
        print("Strip 1: Green, Strip 2: Red")
        pixels_1.fill((0, 255, 0))
        pixels_2.fill((255, 0, 0))
        pixels_1.show()
        pixels_2.show()
        time.sleep(1)

        # Animation: Strip 1 Blue, Strip 2 Green
        print("Strip 1: Blue, Strip 2: Green")
        pixels_1.fill((0, 0, 255))
        pixels_2.fill((0, 255, 0))
        pixels_1.show()
        pixels_2.show()
        time.sleep(1)

        # Animation: Both White
        print("Both White")
        pixels_1.fill((255, 255, 255))
        pixels_2.fill((255, 255, 255))
        pixels_1.show()
        pixels_2.show()
        time.sleep(1)

except KeyboardInterrupt:
    # Turn off all LEDs on exit
    print("\nExiting...")
    pixels_1.fill((0, 0, 0))
    pixels_2.fill((0, 0, 0))
    pixels_1.show()
    pixels_2.show()
