#!/usr/bin/env python3
"""
check_motors.py — Test JETANK wheel motor connectivity via PCA9685 + TB6612FNG.

Hardware path:
    PCA9685 (I2C 0x60, bus 7) → TB6612FNG H-bridge → left/right drive motors

PCA9685 channel mapping for JETANK (Waveshare default):
    Left motor  — PWMA: ch4,  AIN2: ch5,  AIN1: ch6
    Right motor — PWMB: ch7,  BIN2: ch8,  BIN1: ch9

Required module:
    pip install smbus2
    # or in jetbot venv: source ~/jetbot-env/bin/activate && pip install smbus2

Run on Jetson:
    python3 check_motors.py

IMPORTANT:
  - Expansion board switch must be ON (12.6V motor rail required)
  - Elevate the robot off the ground before running — wheels will spin briefly
  - Battery voltage should be above 10.5V (run check_battery.py first)
"""

import sys
import time

try:
    import smbus2
except ImportError:
    sys.exit(
        "ERROR: smbus2 not found.\n"
        "Install: pip install smbus2\n"
        "In venv: source ~/jetbot-env/bin/activate && pip install smbus2"
    )

I2C_BUS      = 7
PCA9685_ADDR = 0x60

# PCA9685 registers
MODE1    = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06  # base register; channel n starts at 0x06 + n*4

# JETANK channel mapping — adjust here if motors behave unexpectedly
MOTOR_CHANNELS = {
    "left":  {"pwm": 4, "in2": 5, "in1": 6},
    "right": {"pwm": 7, "in2": 8, "in1": 9},
}

PWM_FREQ_HZ  = 50    # Hz — safe for TB6612FNG
PWM_MAX      = 4095  # 12-bit PCA9685 resolution
TEST_SPEED   = 0.3   # 30% duty cycle — low speed for safety
TEST_DURATION = 0.6  # seconds each direction


def set_pwm_freq(bus: smbus2.SMBus, freq_hz: int):
    """Set PCA9685 PWM frequency."""
    prescale = round(25_000_000 / (4096 * freq_hz)) - 1
    old_mode = bus.read_byte_data(PCA9685_ADDR, MODE1)
    sleep_mode = (old_mode & 0x7F) | 0x10   # set sleep bit
    bus.write_byte_data(PCA9685_ADDR, MODE1, sleep_mode)
    bus.write_byte_data(PCA9685_ADDR, PRESCALE, prescale)
    bus.write_byte_data(PCA9685_ADDR, MODE1, old_mode)
    time.sleep(0.005)
    bus.write_byte_data(PCA9685_ADDR, MODE1, old_mode | 0xA1)  # restart + auto-increment


def set_channel(bus: smbus2.SMBus, channel: int, on: int, off: int):
    """Set a single PCA9685 channel ON/OFF tick values."""
    reg = LED0_ON_L + channel * 4
    bus.write_i2c_block_data(PCA9685_ADDR, reg, [
        on  & 0xFF, (on  >> 8) & 0xFF,
        off & 0xFF, (off >> 8) & 0xFF,
    ])


def set_motor(bus: smbus2.SMBus, side: str, speed: float):
    """
    Drive one motor at a given speed fraction (-1.0 to 1.0).
    Positive = forward, negative = backward, 0 = stop.
    """
    ch = MOTOR_CHANNELS[side]
    duty = int(abs(speed) * PWM_MAX)

    if speed > 0:       # forward
        set_channel(bus, ch["in1"], 0, PWM_MAX)
        set_channel(bus, ch["in2"], 0, 0)
    elif speed < 0:     # backward
        set_channel(bus, ch["in1"], 0, 0)
        set_channel(bus, ch["in2"], 0, PWM_MAX)
    else:               # stop (coast)
        set_channel(bus, ch["in1"], 0, 0)
        set_channel(bus, ch["in2"], 0, 0)

    set_channel(bus, ch["pwm"], 0, duty)


def stop_all(bus: smbus2.SMBus):
    for side in MOTOR_CHANNELS:
        set_motor(bus, side, 0)


def main():
    print("=" * 42)
    print("  JETANK Motor Connectivity Check")
    print("=" * 42)
    print("  Channels: left (ch4-6), right (ch7-9)")
    print(f"  Speed: {int(TEST_SPEED * 100)}% | Duration: {TEST_DURATION}s per step")
    print()

    # --- Open I2C bus ---
    try:
        bus = smbus2.SMBus(I2C_BUS)
    except FileNotFoundError:
        sys.exit(f"ERROR: /dev/i2c-{I2C_BUS} not found.")
    except PermissionError:
        sys.exit(f"ERROR: Permission denied on /dev/i2c-{I2C_BUS}. Try: sudo python3 check_motors.py")

    # --- Verify PCA9685 is present ---
    try:
        bus.read_byte_data(PCA9685_ADDR, MODE1)
        print(f"  PCA9685 found at 0x{PCA9685_ADDR:02X} on bus {I2C_BUS} ... OK")
    except OSError:
        bus.close()
        sys.exit(
            f"ERROR: PCA9685 not found at 0x{PCA9685_ADDR:02X} on bus {I2C_BUS}.\n"
            "Check that the expansion board switch is ON."
        )

    set_pwm_freq(bus, PWM_FREQ_HZ)
    stop_all(bus)

    # --- Test sequence ---
    try:
        print("\n  [1/3] Both motors FORWARD ...")
        set_motor(bus, "left",  TEST_SPEED)
        set_motor(bus, "right", TEST_SPEED)
        time.sleep(TEST_DURATION)
        stop_all(bus)
        time.sleep(0.3)

        print("  [2/3] Both motors BACKWARD ...")
        set_motor(bus, "left",  -TEST_SPEED)
        set_motor(bus, "right", -TEST_SPEED)
        time.sleep(TEST_DURATION)
        stop_all(bus)
        time.sleep(0.3)

        print("  [3/3] Left motor only (pivot check) ...")
        set_motor(bus, "left",  TEST_SPEED)
        set_motor(bus, "right", 0)
        time.sleep(TEST_DURATION)
        stop_all(bus)

    except OSError as e:
        stop_all(bus)
        bus.close()
        sys.exit(f"ERROR during motor command: {e}")

    bus.close()

    print()
    print("  Sequence complete.")
    print()
    print("  Expected results:")
    print("    Step 1 — both tracks spin forward")
    print("    Step 2 — both tracks spin backward")
    print("    Step 3 — only left track spins")
    print()
    print("  If tracks did NOT move:")
    print("    - Confirm expansion board switch is ON")
    print("    - Run check_battery.py to verify voltage > 10.5V")
    print("    - Check channel mapping constants at top of this script")
    print("=" * 42)


if __name__ == "__main__":
    main()
