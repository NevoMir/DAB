# Passive Buzzer Connection Guide

## 1. I2C Bus Sharing (The "Why")
**Yes, you MUST use GPIO 2 and GPIO 3 for both the Servo Driver and the LCD.**
*   **GPIO 2 (Pin 3)** = SDA (Serial Data)
*   **GPIO 3 (Pin 5)** = SCL (Serial Clock)

These pins are a **bus**. You can connect multiple devices to the same two pins. Think of it like a power strip where multiple appliances plug into the same wall socket.
*   **Servo Driver HAT**: Uses address `0x40`.
*   **LCD Implementation**: Uses address `0x3E` (or `0x60` depending on the model).
Since their addresses are different, they will not interfere with each other. Just wire them in parallel (connect LCD SDA to RPi SDA, LCD SCL to RPi SCL).

## 2. Passive Buzzer Wiring
You are using a **Passive Buzzer** and an **NPN Transistor (SS8050)**.
*   **Passive Buzzer**: Needs a PWM signal (oscillating current) to make sound.
*   **Transistor**: Acts as a switch to drive the buzzer because the Pi's GPIO pins are too weak to drive it directly reliably.

### Components
*   Raspberry Pi
*   Passive Buzzer
*   SS8050 NPN Transistor
*   1kΩ Resistor (highly recommended for the Base pin)
*   Jumper wires

### Wiring Diagram
We will use **GPIO 17 (Physical Pin 11)** for the signal.

| Component Pin | Connect To | Description |
| :--- | :--- | :--- |
| **Transistor Collector (C)** | **Buzzer (-)** | The negative/shorter leg of the buzzer. |
| **Transistor Base (B)** | **GPIO 17** | Connect via a **~1kΩ resistor** if possible. Pin 11 on the Pi. |
| **Transistor Emitter (E)** | **GND** | Any Ground pin on the Pi (e.g., Pin 9). |
| **Buzzer (+)** | **5V (or 3.3V)** | The positive/longer leg. 5V (Pin 2 or 4) makes it louder. |

**Visual Check for SS8050 (Flat side facing you, pins down):**
*   Left: **E** (Emitter) -> GND
*   Middle: **B** (Base) -> GPIO 17
*   Right: **C** (Collector) -> Buzzer (-)

## 3. Software
Run the expected python script:
```bash
python3 passive_buzzer.py
```
This script will play a melody to confirm the setup works.
