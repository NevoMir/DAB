import RPi.GPIO as GPIO
import time

# --- CONFIGURATION ---
BUZZER_PIN = 17  # GPIO 17 (Physical Pin 11)

# --- SETUP ---
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

# --- MUSIC FUNCTIONS ---
def play_tone(pwm, frequency, duration):
    """
    Plays a tone at a specific frequency for a duration.
    :param pwm: The PWM object
    :param frequency: Frequency in Hz (e.g., 440 for A4)
    :param duration: Duration in seconds
    """
    if frequency <= 0:
        # Rest
        pwm.stop()
        time.sleep(duration)
        pwm.start(50) # Restart duty cycle for next note
    else:
        pwm.ChangeFrequency(frequency)
        pwm.start(50)  # 50% duty cycle is standard for square wave
        time.sleep(duration)
        pwm.stop()

def destroy():
    GPIO.cleanup()

# --- MELODY ---
# Notes and frequencies (Hz)
NOTES = {
    'C4': 261, 'D4': 294, 'E4': 329, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 493,
    'C5': 523
}

def main():
    setup()
    
    # Initialize PWM on the buzzer pin
    # Start with an initial frequency (will be changed immediately)
    pwm = GPIO.PWM(BUZZER_PIN, 440) 
    
    print(f"Playing sound on GPIO {BUZZER_PIN}...")
    print("Press CTRL+C to stop.")

    try:
        # Simple Scale
        print("Playing Scale...")
        scale = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
        for note in scale:
            play_tone(pwm, NOTES[note], 0.3)
            time.sleep(0.05) # Short gap between notes

        time.sleep(0.5)

        # Siren effect
        print("Playing Siren...")
        pwm.start(50)
        for _ in range(3):
            for freq in range(400, 800, 10):
                pwm.ChangeFrequency(freq)
                time.sleep(0.01)
            for freq in range(800, 400, -10):
                pwm.ChangeFrequency(freq)
                time.sleep(0.01)
        pwm.stop()
        
        print("Done.")

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        destroy()

if __name__ == '__main__':
    main()
