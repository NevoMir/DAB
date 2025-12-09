
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
while True:
    if GPIO.input(4) == GPIO.HIGH:
        print("Button Pressed")
