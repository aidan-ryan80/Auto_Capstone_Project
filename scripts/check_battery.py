#!/usr/bin/env python3
"""
check_battery.py — Read JETANK expansion board battery voltage via INA219.

Hardware: INA219 current sensor at I2C address 0x41, bus 7.

Required module:
    pip install smbus2
    # or in jetbot venv: source ~/jetbot-env/bin/activate && pip install smbus2

Run on Jetson:
    python3 check_battery.py

Note: expansion board switch must be ON for a valid voltage reading.
If the switch is off, voltage will read ~0V (motor rail is dead).
"""

import sys

try:
    import smbus2
except ImportError:
    sys.exit(
        "ERROR: smbus2 not found.\n"
        "Install: pip install smbus2\n"
        "In venv: source ~/jetbot-env/bin/activate && pip install smbus2"
    )

I2C_BUS     = 7
INA219_ADDR = 0x41

REG_BUS_VOLTAGE = 0x02  # INA219 bus voltage register

# 3S 18650 pack thresholds
V_MAX = 12.6   # fully charged (4.2V per cell)
V_MIN = 10.5   # practical empty (3.5V per cell)


def read_bus_voltage(bus: smbus2.SMBus) -> float:
    """Bus voltage in volts. INA219 LSB = 4 mV, value is in bits [15:3]."""
    raw = bus.read_i2c_block_data(INA219_ADDR, REG_BUS_VOLTAGE, 2)
    value = ((raw[0] << 8) | raw[1]) >> 3
    return value * 0.004


def estimate_percentage(voltage: float) -> int:
    pct = (voltage - V_MIN) / (V_MAX - V_MIN) * 100
    return max(0, min(100, round(pct)))


def progress_bar(pct: int, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def main():
    try:
        bus = smbus2.SMBus(I2C_BUS)
    except FileNotFoundError:
        sys.exit(f"ERROR: /dev/i2c-{I2C_BUS} not found. Is the expansion board connected?")
    except PermissionError:
        sys.exit(f"ERROR: Permission denied on /dev/i2c-{I2C_BUS}. Try: sudo python3 check_battery.py")

    try:
        voltage = read_bus_voltage(bus)
    except OSError as e:
        sys.exit(
            f"ERROR: Could not read INA219 at 0x{INA219_ADDR:02X} on bus {I2C_BUS}: {e}\n"
            "Ensure the expansion board switch is ON."
        )
    finally:
        bus.close()

    pct = estimate_percentage(voltage)

    print("=" * 42)
    print("  JETANK Battery Status (3S 18650 pack)")
    print("=" * 42)
    print(f"  Voltage : {voltage:.2f} V")
    print(f"  Charge  : {pct:3d}%  {progress_bar(pct)}")
    print(f"  Range   : {V_MIN}V (empty) — {V_MAX}V (full)")

    if voltage < 10.0:
        print("\n  !! CRITICAL: Voltage dangerously low — charge immediately.")
    elif voltage < V_MIN:
        print("\n  WARNING: Below safe threshold — charge batteries now.")
    elif pct < 20:
        print(f"\n  WARNING: Low battery ({pct}%) — charge soon.")
    elif voltage < 0.5:
        print("\n  NOTE: Voltage near zero — is the expansion board switch ON?")
    else:
        print("\n  Status  : OK")

    print("=" * 42)


if __name__ == "__main__":
    main()
