# Capstone Poster Content — JetBot Orin Nano Autonomous Driving

---

## At a Glance

**Project:** Autonomous driving robot using camera fusion for perception and control

**Platform:** Waveshare JETANK AI Kit + NVIDIA Jetson Orin Nano Super (JetPack 6.2)

**Tasks:**
- **Task C:** Hardware assembly, platform integration, and system validation
- **Task B:** Real-time camera fusion — lane detection + object (YOLO) detection merged into a single per-frame perception state
- **Task A:** Safety-gated control policy that maps fused perception to steering/throttle commands

**Team:** 4 members

---

## Motivation & Introduction

### Why edge AI robotics?
Autonomous mobile robots that run inference locally (not in the cloud) are critical for real-time applications where latency, privacy, and connectivity cannot be guaranteed — warehouses, hospitals, agricultural inspection, and last-mile delivery. The NVIDIA Jetson family provides GPU-accelerated edge computing in a form factor suitable for small robots.

### Why camera fusion?
Individual perception modalities are fragile:
- **Lane detection alone** fails when obstacles block the road markings
- **Object detection alone** cannot determine the robot's position within a lane
- **Fusing both** gives a complete scene state per frame: lane offset + obstacle class/position/distance → enables robust control decisions

### The JetBot gap
The widely-used NVIDIA JetBot reference platform targets the older Jetson Nano (2019, JetPack 4.x). Our project uses the newer **Jetson Orin Nano Super** (2024, JetPack 6.x), which has significantly different hardware interfaces, power requirements, kernel configuration, and OS packaging. Existing guides and tutorials required substantial adaptation — this project documents a complete bring-up path for the Orin generation.

---

## Materials

### Hardware
| Component | Model/Spec | Purpose |
|-----------|------------|---------|
| Main compute | NVIDIA Jetson Orin Nano Super (8 GB) | GPU-accelerated inference, 6× ARM Cortex-A78 cores, Ampere GPU with 1024 CUDA cores |
| Chassis | Waveshare JETANK AI Kit | Tank-style chassis with continuous tracks, TB6612FNG dual H-bridge motor driver, PCA9685 PWM controller |
| Camera | Waveshare IMX219-160 (CSI) | 160° FOV, 8 MP, connected via MIPI CSI-2 ribbon to CAM0 |
| Servos | Feetech SCS15-AP (×5) | Serial bus servos for 5-DOF robotic arm (currently 2 mounted: base rotation + camera tilt) |
| Display | SSD1306 OLED (128×32) | System status (IP, CPU, RAM, component health) |
| Power (Jetson) | Veger T100 100W USB-C PD power bank + PD trigger cable (15V, 5.5×2.5mm barrel) | Independent 9-20V supply for Orin mainboard |
| Power (motors) | 18650 batteries (3S, ~12.6V) via JETANK expansion board | Motor/servo rail only |
| Sensors | INA219 current sensor | Monitor battery voltage and current draw |
| Networking | Intel Wireless 8265/8275 (PCIe) | WiFi 5 via `wlP1p1s0` (requires DKMS backport driver on JetPack 6.x) |

### Software Stack
| Component | Version/Detail |
|-----------|---------------|
| OS | JetPack 6.2 (L4T R36.4.4, kernel 5.15.148-tegra) |
| GPU compute | CUDA 12.6, cuDNN 9.3.0.75, TensorRT 10.3.0.30 |
| ML framework | PyTorch via Docker containers (moatazsawi/jetbot-orin) |
| Computer vision | OpenCV 4.8.0 (built-in), GStreamer with nvarguscamerasrc |
| Motor control | PCA9685 driver (smbus2), TB6612FNG via custom Robot class |
| Servo control | Feetech SCS SDK (SCSCtrl, 1 Mbps on /dev/ttyTHS1) |
| Display | luma.oled (SSD1306, I2C bus 7, systemd service) |
| Container runtime | Docker 28.2.2 |

---

## Results

### Hardware Bring-Up (Task C)

**Resolved issues (10 total):**

| Category | Problem | Root Cause | Fix |
|----------|---------|------------|-----|
| OS | Image wouldn't boot | Used JetPack 4.x/5.x images for Orin hardware | Flashed JetPack 6.2 |
| Networking | No WiFi interface | `iwlwifi` module stripped from JetPack 6.x kernel | `backport-iwlwifi-dkms` compiled via DKMS |
| Display | No GUI on boot | `/usr/sbin/gdm3` binary missing from JetPack image | `apt install --reinstall gdm3` |
| Camera | No `/dev/video0` | IMX219 driver activated via device tree overlay, not loadable module | Added `OVERLAYS ... imx219-A.dtbo` to `extlinux.conf` |
| OLED | Blank display | Hardcoded I2C bus 1, `wlan0`, unavailable libraries (`qwiic`, `Adafruit_SSD1306`) | Rewrote with `luma.oled`, bus 7, `wlP1p1s0` |
| Servos | Aggressive spinning, cable tangling | Centre positions drifted from factory 512; `servoInt.py` missing `import time` | Updated `servoInit` values; added `import time` |
| Python | `pip` broken | Version conflict between `python3-setuptools` and `python3-pkg-resources` | `curl https://bootstrap.pypa.io/get-pip.py | python3` bypassed apt |

**Remaining blocker:** The JETANK expansion board was designed for Jetson Nano (5V via GPIO). The Orin Nano requires 9-20V via DC barrel — the boards must be powered independently. Power bank solution identified (Veger T100 + PD trigger cable) but not yet procured.

### Drive Motor Investigation (Critical — In Progress)

**Symptom:** All `robot.forward()` / `robot.left()` commands execute without errors but produce zero motor movement.

**Bugs found and fixed:**
1. **PCA9685 FULL_ON bug:** `set_pwm(channel, 0, 0)` sets ON=OFF=0, which per the datasheet forces the pin always HIGH (ON has priority). This kept the TB6612FNG direction pins in brake mode. Fixed to `set_pwm(channel, 0, 4096)` (FULL_OFF).
2. **Wrong channel mapping:** Motor.py used Adafruit MotorHAT channel layout instead of Waveshare JETANK layout. Fixed to `{1: (0,1,2), 2: (5,3,4)}`.

**Neither fix produced movement.** Exhaustive brute-force scan of all plausible PCA9685 channel combinations with correct FULL_OFF logic and STBY channels probed — no movement on any combination.

**Ruled out:** PCA9685 present on bus 7 ✓, battery at 11.85V ✓, motors connected ✓, import path correct ✓, no I2C errors ✓.

**Unverified:** PCA9685 register read-back, TB6612FNG STBY pin wiring, VM pin voltage, expansion board schematic.

### Perception Fusion (Task B — Not Started)
Pipeline design is complete. Per-frame fused state format:
```json
{
  "lane_offset": 0.10,
  "lane_conf": 0.84,
  "obstacle": {"class": "person", "conf": 0.92, "distance_m": 1.7},
  "risk_level": "high",
  "action_hint": "stop"
}
```
Implementation is blocked by power solution and motor control resolution.

### Control Policy (Task A — Not Started)
Logic designed:
- Lane centered + clear → forward
- Lane offset → steering correction
- High risk or low confidence → slow/stop
- Safety gates: confidence threshold, obstacle-distance threshold, manual e-stop
Implementation blocked by Task B completion.

---

## Conclusion

We successfully brought up a **Jetson Orin Nano Super** on the **Waveshare JETANK** platform despite the hardware being designed for a different Jetson generation. Ten distinct system-level issues were diagnosed and resolved across OS compatibility, kernel drivers, desktop environment, camera, display, serial servos, and package management — providing a documented bring-up path for future Orin-based JetBot projects.

Two critical blockers remain:
1. **Power architecture:** The Orin Nano cannot be powered through the JETANK board. An independent USB-C PD power bank solution is identified but untested.
2. **Drive motor control:** Despite fixing two bugs in the PCA9685 motor driver code and an exhaustive channel scan, motors do not respond. The root cause likely requires hardware-level probing (multimeter verification of TB6612FNG supply voltage, STBY pin state, and PCA9685 register read-back) or access to the expansion board schematic.

The perception fusion pipeline (Task B) and autonomous control policy (Task A) are fully designed at the architectural level but cannot be implemented and tested until the power and motor blockers are resolved.

---

## Recommendations & Discussion

### For resolving the drive motor issue
1. **Register read-back verification:** Use `i2cget` to read PCA9685 LED0-15 registers after writes and confirm values stick. This is the simplest test to rule out an I2C communication problem.
2. **Multimeter probing:** With motors commanded to move, probe TB6612FNG pins — VM (motor supply voltage), STBY (should be >2V for enable), and IN1/IN2 (should toggle between 0V and 3.3V depending on direction). If VM is 0V, the battery rail isn't reaching the driver.
3. **Expand the channel brute-force:** Include PCA9685 channels 8-15 in every combination (not just STBY candidates). The JETANK may use non-standard channel assignment not documented in any public repo.
4. **Direct motor test:** Wire one motor directly to the 18650 battery (briefly) to confirm the motors themselves are functional and not damaged.
5. **Request schematic:** Contact Waveshare support for the JETANK expansion board schematic or at least the PCA9685 → TB6612FNG pin mapping.

### For the power blocker
- Procure the Veger T100 and PD trigger cable (5.5×2.5mm, set to 15V) as soon as possible
- Alternatively, evaluate the **Waveshare UPS Module (C)** designed for Jetson Orin with 21700 cells — provides regulated output and UPS functionality in a single package
- Physical mount: secure the power bank low and centred on the chassis for balance

### For future work on Orin-based JetBot projects
- **Use JetPack 6.2 as the baseline** — earlier versions are incompatible with Orin hardware
- **Add the IMX219 overlay and install `backport-iwlwifi-dkms`** as standard first-boot steps after flashing
- **Replace `wlan0` references** — JetPack 6.x uses predictable interface naming (`wlP1p1s0`)
- **Check I2C bus number** — the JETANK expansion board lives on bus 7, not the default bus 1
- **Bootstrap pip with the PyPA script** — apt-managed pip is broken on JetPack 6.x
- **Allocate storage headroom** — the 28 GiB microSD fills quickly (83% used); consider an NVMe SSD upgrade
