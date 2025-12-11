# Connecting LCD1602 (I2C) to Raspberry Pi

## The Challenge
You are already using the following pins for another device (likely a Servo HAT):
*   **Pin 1 (3.3V)** -> In use
*   **Pin 3 (SDA)** -> In use
*   **Pin 5 (SCL)** -> In use
*   **Pin 6 (GND)** -> In use

## The Solution: Parallel Connection (Splitting)
The **I2C Protocol** (used by Pins 3 & 5) is designed to handle multiple devices on the same wires, as long as they have different "addresses".
*   Servo HAT usually uses Address `0x40`.
*   LCD1602 usually uses Address `0x27` (or `0x3F`).

**You do NOT need new pins.** You simply need to connect the LCD's SDA and SCL wires to the *same* physical pins as your other device.

## Step-by-Step Wiring
1.  **GND (Ground)**
    *   Connect LCD `GND` to **ANY** Ground pin on the Pi.
    *   *Options*: Pin 6 (Shared), Pin 9, 14, 20, 25, 30, 34, 39.
2.  **VCC (Power)**
    *   **CRITICAL**: Most LCD1602 modules require **5V** to light up the backlight fully. Pin 1 is only 3.3V.
    *   Connect LCD `VCC` to **Pin 2** or **Pin 4** (5V Pins).
3.  **SDA (Data)**
    *   Connect LCD `SDA` to **Pin 3**.
    *   *Note*: If Pin 3 is occupied by a connector, you can splice the wire, use a breadboard, or if your Hat has "breakout pins" (extra holes labeled SDA/SCL), plug it in there.
4.  **SCL (Clock)**
    *   Connect LCD `SCL` to **Pin 5**.
    *   *Note*: Same as SDA.

## Software Setup
On your Raspberry Pi terminal:

1.  **Enable I2C** (if not already done):
    ```bash
    sudo raspi-config
    # Select Interface Options -> I2C -> Yes
    ```

2.  **Install Library**:
    ```bash
    # Try installing normally first
    pip3 install RPLCD smbus2

    # If you get "externally-managed-environment" error:
    # Option A (Recommended): Create a virtual environment
    python3 -m venv myenv
    source myenv/bin/activate
    pip install RPLCD smbus2

    # Option B (Quick & Dirty): Break system packages
    pip3 install RPLCD smbus2 --break-system-packages
    ```

3.  **Find Your Address**:
    Run this command to see connected devices:
    ```bash
    i2cdetect -y 1
    ```
    *   You should see a grid. Look for numbers like `27` (LCD) and `40` (Servo).
