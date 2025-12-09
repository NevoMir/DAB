from gpiozero import Button
from signal import pause

# Initialize the button on GPIO 4
# Original code used PUD_DOWN and checked for HIGH, so we use pull_up=False
# This expects the button to connect GPIO 4 to 3.V when pressed
try:
    button = Button(4, pull_up=False)
    print("Button initialized on GPIO 4 (Pull-Down/Active High).")
    print("Press the button to see output (Ctrl+C to exit).")
    
    button.when_pressed = lambda: print("Button Pressed")
    
    pause()

except Exception as e:
    print(f"An error occurred: {e}")
    print("\nIf you see an error about 'pin factory', please run:")
    print("pip install rpi-lgpio")
