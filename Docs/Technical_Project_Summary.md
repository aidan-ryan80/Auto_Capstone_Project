# Technical Project Summary — JetBot Orin Nano Capstone

## Overview

Building an autonomous JetBot using a **Waveshare JETANK AI Kit** paired with a **Jetson Orin Nano Super** (JetPack 6.2 / L4T R36.4.4, kernel `5.15.148-tegra`). Three capstone tasks: **C** (hardware assembly + integration), **B** (camera fusion for perception), **A** (camera fusion for driving control).

---

## Table of Contents

1. [Platform Identification & OS Flashing](#1-platform-identification--os-flashing)
2. [WiFi Driver (Intel 8265 + JetPack 6.x)](#2-wifi-driver-intel-8265--jetpack-6x)
3. [Desktop Environment (GDM3)](#3-desktop-environment-gdm3)
4. [Python/pip Dependency Conflicts](#4-pythonpip-dependency-conflicts)
5. [Power Architecture (Orin vs. Nano incompatibility)](#5-power-architecture-orin-vs-nano-incompatibility)
6. [JETANK Software Installation](#6-jetank-software-installation)
7. [Servo Calibration (Feetech SCS15-AP)](#7-servo-calibration-feetech-scs15-ap)
8. [I2C Bus & Expansion Board](#8-i2c-bus--expansion-board)
9. [OLED Display](#9-oled-display)
10. [CSI Camera (IMX219-160)](#10-csi-camera-imx219-160)
11. [Drive Motor Investigation (Unresolved)](#11-drive-motor-investigation-unresolved)
12. [Repository Layout & Docker Workflow](#12-repository-layout--docker-workflow)

---

## 1. Platform Identification & OS Flashing

### Problem: Wrong OS images for Orin hardware
The hardware was initially assumed to be a **Jetson Nano (4GB)**, but is actually a **Jetson Orin Nano Super** (module P3767, carrier board P3768). This meant all legacy JetPack 4.x / 5.x images failed to boot.

### Failed images tried
| Image | Outcome |
|-------|---------|
| `jetbot-043_nano-4gb-jp45` | Stuck at boot (kernel panic) |
| `jetson-nano-jp461-sd-card-image` | Stuck at boot |
| `jp60dp-orin-nano-sd-card-image` | Stuck at boot |
| `JP512-orin-nano-sd-card-image` | Stuck at boot |

### Working image
`jp62-orin-nano-sd-card-image` (JetPack 6.2, kernel `5.15.148-tegra`).

### Board identification
The model string from device tree: `NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super`.

### Flashing notes
- Rufus cannot write the raw partition image — use **Balena Etcher**.
- On Windows, **Diskpart** must be used to clean the SD card before flashing (standard format isn't enough for raw images).
- QSPI firmware update **not required** when coming from an existing JetPack 6.x install.

### Boot failure due to image mismatch
Session 2026-03-12: Initial OS image suggested by Tingting failed to boot. Session 2026-03-24: identified the root incompatibility — legacy JetBot Nano JP4.5 images and JetPack 4.x/5.x images target a different SoC architecture (Tegra X1 vs. Orin AGX). The Orin Nano requires JetPack 6.0+.

---

## 2. WiFi Driver (Intel 8265 + JetPack 6.x)

### Root cause
JetPack 6.x ships with a **stripped-down kernel** (kernel variant: `oot`, out-of-tree) that does not include the `iwlwifi` kernel module. The Intel Wireless 8265/8275 card is physically present on PCIe (`0001:01:00.0`) but produces no wireless interface.

### Diagnosis
```bash
lspci | grep -i network       # Card detected: Intel 8265/8275 (rev 78)
modinfo iwlwifi               # ERROR: Module not found
ip link show                  # No wlan/wl interface
```

### Fix
```bash
sudo apt install backport-iwlwifi-dkms
# Built the module against the running 5.15.148-tegra kernel via DKMS
sudo reboot
```

After reboot, `wlP1p1s0` appeared. Interface uses **predictable naming** (not `wlan0`), which breaks scripts that hardcode `wlan0`.

### Additional issue: DKMS install skipped
On the initial attempt, DKMS built the module but did **not** install it. Required an explicit:
```bash
sudo dkms install backport-iwlwifi/11510 -k 5.15.148-tegra
```

### WiFi auto-connect
Configured via `nmcli connection modify "DIGILAB" connection.autoconnect yes`. Jetson obtains `10.26.193.10` via DHCP on the DIGILAB network.

### Alternatives considered
- **USB WiFi dongle** with a supported chipset (Realtek RTL8812AU or MediaTek MT7612U) — would bypass kernel module issue entirely
- **Travel router** in client-bridge mode, connected via Ethernet and carried on the chassis
- **Phone USB tethering** — provides internet but not a dedicated LAN address for SSH

Chosen approach (DKMS backport) was preferred because it uses the onboard hardware without adding extra dongles.

---

## 3. Desktop Environment (GDM3)

### Symptom
GDM3 service showed `active (exited)` but no graphical session appeared on the monitor.

### Root cause
`/usr/sbin/gdm3` binary was **missing** from the JetPack image. The init script checks `test -x $DAEMON || exit 0`, which silently exits when the binary doesn't exist. The systemd service had `RemainAfterExit=yes`, masking the failure.

### Diagnosis
```bash
ls -la /usr/sbin/gdm3       # File not found
sudo systemctl status gdm3  # Shows "active (exited)" — misleading
```

### Fix
```bash
sudo apt install --reinstall gdm3
```
Verified: `/usr/sbin/gdm3` present, manual X server startup confirmed working at 2560×1440 with NVIDIA DRM extensions.

---

## 4. Python/pip Dependency Conflicts

### Problem: apt-managed pip is broken
`sudo apt install python3-pip` fails with a version conflict between `python3-setuptools` and `python3-pkg-resources`. `dist-upgrade` does not resolve it — packages are held.

### Workaround: venv
```bash
python3 -m venv ~/jetbot-env
source ~/jetbot-env/bin/activate
pip install <package>
```
This works but requires activation before every session.

### Proper fix: bootstrap pip directly
```bash
curl https://bootstrap.pypa.io/get-pip.py | python3
```
This bypasses apt entirely. After this, `pip3 install <package>` works system-wide.

---

## 5. Power Architecture (Orin vs. Nano incompatibility)

### Problem: JETANK cannot power the Orin
The JETANK expansion board was designed for the original Jetson Nano, which accepts **5V via GPIO header pins**. The Jetson Orin Nano Super requires **9–20V via DC barrel jack** and does NOT accept 5V via GPIO.

### Architecture
```
Path 1: Veger T100 USB-C PD power bank
         → USB-C to USB-C cable
         → PD trigger cable (set to 15V)
         → 5.5×2.5mm barrel plug
         → Jetson Orin Nano DC barrel jack

Path 2: JETANK 18650 batteries (3S, ~12.6V)
         → Expansion board switch
         → Motors, servos, TB6612FNG, SY8286
```

### GPIO 5V backfeed behavior
Jetson GPIO pins 2 and 4 (5V) are **always live** when the Jetson is powered, regardless of the expansion board switch. This powers the OLED, INA219, and PCA9685 via I2C whenever the Jetson is on. The expansion board switch only controls the 12.6V motor/servo rail. This is safe — the two voltage rails are isolated by hardware.

### Critical: USB-C PD requirement
Must use **USB-C to USB-C** between the power bank and the PD trigger cable. USB-A to USB-C bypasses Power Delivery negotiation — the bank falls back to 5V and the Jetson won't power on.

### Power-on sequence
Always power expansion board **first**, then Jetson. Reason: Jetson initializes I2C and serial buses at boot. If the expansion board is unpowered, bus lines float and devices may not be detected.

### Alternatives considered
- **3S LiPo battery** (11.1–12.6V) with correct barrel connector — could directly power the Jetson without PD negotiation
- **19V laptop-style portable power bank** — sufficient voltage but bulkier
- **Waveshare UPS Module (C)** — designed specifically for Jetson Orin with 21700 cells, provides regulated output and UPS functionality (cleanest solution if available)

### Electrical behaviour: ground sharing
The two power rails (battery → motors, power bank → Jetson) share only a **common ground** through the GPIO header. This is necessary for I2C and serial communication between the Jetson and expansion board devices, but means the robot has two separate voltage domains.

### Current status
Power solution identified (Veger T100 + PD trigger cable) but **not yet procured/tested** — this is the critical blocker for Tasks C and beyond.

---

## 6. JETANK Software Installation

### Install sequence
```bash
sudo ./config.sh jetbot    # Configures device tree overlays, reboots
sudo ./install.sh          # Installs Python packages, moves files
```

### Issues encountered on JetPack 6.2

| Issue | Severity | Cause |
|-------|----------|-------|
| `apt-news.service` not found | Harmless | Systemd service not present in JetPack 6.2 |
| `esm-cache.service` not found | Harmless | Ubuntu Pro ESM service not configured |
| Duplicate apt sources.list entries | Warning | Install script appends without checking |
| `cp: cannot create directory '//workspace/jetbot/notebooks'` | Harmless | Notebooks path doesn't exist on bare JetPack 6.2 |
| `import time` missing from `servoInt.py` | Bug | Calibration script crashes at runtime |

---

## 7. Servo Calibration (Feetech SCS15-AP)

### Hardware
- **Type:** Feetech SCS15-AP serial bus servos
- **Protocol:** SCS (protocol_end = 1)
- **Baudrate:** 1,000,000
- **Port:** `/dev/ttyTHS1`
- **IDs:** 1–5 (EEPROM-persistent)

### Symptom: aggressive spinning & cable tangling
On first command, servos spun aggressively to wrong positions. Servo 1 (base rotation) wrapped its cable around the chassis, requiring physical disassembly to free.

### Initial calibration drift
After physical reassembly, centre positions drifted from factory default of 512. Actual centre values were read back via a serial bus scan on `/dev/ttyTHS1` at 1,000,000 baud:
```python
servoInit = [None, 1021, 512, 512, 512, 811]
```

This must be updated in **two locations** — the installed package shadows the source repo:
- `/home/jetbot-04/.local/lib/python3.10/site-packages/SCSCtrl/TTLServo.py` (active import — run `python3 -c "import SCSCtrl.TTLServo; print(SCSCtrl.TTLServo.__file__)"` to confirm)
- `/home/jetbot-04/JETANK/SCSCtrl/TTLServo.py` (source repo, used for re-install)

### servoInt.py missing import
The Waveshare calibration script `~/JETANK/servoInt.py` uses `time.sleep()` but lacks `import time`. Fix:
```bash
sed -i '3a import time' ~/JETANK/servoInt.py
```

### Constraints
- Servo ID 1 (base rotation) has **no physical stop** — max ±80 degrees from centre or cables tangle.
- Always use speed 30 for initial testing; 150 only after motion is confirmed safe.
- Alternatives considered: re-flashing servo EEPROM with new centre positions (rejected as overkill — software calibration in `servoInit` is sufficient).

---

## 8. I2C Bus & Expansion Board

### Bus identification
The correct I2C bus is **bus 7**, not the default bus 1 that most tutorials assume:
```bash
sudo i2cdetect -y -r 7
```

### Devices confirmed present
| Address | Device | Function |
|---------|--------|----------|
| `0x3c` | SSD1306 | OLED display |
| `0x41` | INA219 | Current/voltage sensor |
| `0x60` | PCA9685 | PWM motor controller |
| `0x70` | PCA9685 | Broadcast address |

---

## 9. OLED Display

### Dependencies
```bash
sudo python3 -m pip install luma.oled psutil
```
Note: `sudo python3 -m pip` (not `sudo pip3`) — `pip3` is not in root's PATH.

### Problems with original stats.py
The original script from the NVIDIA JetBot repo had three issues:
1. **Hardcoded `i2c_bus=1`** — needed bus 7
2. **Checked for `wlan0`** — interface is `wlP1p1s0` on JetPack 6.x
3. **Imported unavailable libraries** — `qwiic` and `Adafruit_SSD1306` not installed; replaced with `luma.oled`

### Systemd service
Service file at `/etc/systemd/system/jetbot_stats.service`. Key detail: `ExecStart` must call the script directly by path, not via `python3 -m` module syntax.

---

## 10. CSI Camera (IMX219-160)

### Hardware
- **Sensor:** IMX219-160
- **Interface:** CSI ribbon (FFC), CAM0 port
- **I2C:** Address `0x10` on bus 9

### Root cause: camera not detected
The IMX219 kernel module is **not a loadable module** on JetPack 6.2 — it is activated via **device tree overlay**. Without the overlay in `extlinux.conf`, the driver never loads and no `/dev/video*` devices appear.

Diagnostic message:
```
dmesg | grep imx219
# "driver not enabled, cannot register any devices"
```

### Fix: add overlay to extlinux.conf
```bash
sudo vim /boot/extlinux/extlinux.conf
```

Added to the `LABEL primary` section:
```
OVERLAYS /boot/tegra234-p3767-camera-p3768-imx219-A.dtbo
```

- `-A` overlay = CAM0 (sensor-id=0, used by JETANK notebooks)
- `-C` overlay = CAM1 (if cable is moved to CAM1)

### Verification
```bash
ls /dev/video*                   # /dev/video0 appears
gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! \
  'video/x-raw(memory:NVMM),width=1280,height=720' ! \
  nvvidconv ! jpegenc ! filesink location=~/test_snap.jpg
```

### CSI connector fragility
The ZIF connector latch is extremely delicate:
- Lift latch **upward** 1–2mm (fingernail or plastic spudger only)
- Insert cable with **metal contacts facing down**
- Press latch flat — never use metal tools near it

---

## 11. Drive Motor Investigation (Unresolved)

### Hardware
- **Driver chip:** TB6612FNG dual H-bridge
- **PWM controller:** PCA9685 at I2C address `0x60` on bus 7
- **Power:** 18650 batteries at 11.85V (79%), switch ON

### Software stack
```python
from jetbot import Robot    # resolves to ~/jetbot_waveshare/jetbot/robot.py
```
`robot.py` uses `PCA9685(address=0x60, bus=7)` — confirmed correct.
`Robot()` instantiates without errors. All motion commands (`forward()`, `left()`, etc.) run without errors.
**But motors produce zero physical movement.**

### Fix 1: pca9685.py set_pin(0) bug
Original code used `set_pwm(channel, 0, 0)` for value=0. Per PCA9685 datasheet, when ON=OFF=0, **ON has priority** → pin forced HIGH. This means IN2 was never pulled LOW, putting TB6612FNG in **brake mode**.

Fixed to:
```python
if value == 0:
    self.set_pwm(channel, 0, 4096)  # FULL_OFF bit
```

### Fix 2: motor.py channel mapping
Original mapping followed Adafruit MotorHAT layout:
```python
1: (2, 3, 4),   # Wrong for Waveshare JETANK
2: (7, 6, 5),
```

Updated to Waveshare standard:
```python
1: (0, 1, 2),   # PWMA=0, AIN1=1, AIN2=2 (left motor)
2: (5, 3, 4),   # PWMB=5, BIN1=3, BIN2=4 (right motor)
```

### Result: neither fix produced movement

### Brute force scan
Tried all common PCA9685 channel triplets with correct FULL_OFF logic and STBY channels 8, 9, 12, 13, 14, 15 set HIGH — no movement on any combination.

### What has been ruled out
- **PCA9685 not present** — confirmed at address `0x60` on I2C bus 7 via `i2cdetect` ✓
- **Power to expansion board** — INA219 reports 11.85V (79% charge) ✓
- **Motor physical connections** — motors verified plugged into correct terminals ✓
- **Python import path** — `from jetbot import Robot` resolves to `~/jetbot_waveshare/jetbot/robot.py` ✓
- **PCA9685 not receiving commands** — no I2C errors thrown on any `set_pwm` call ✓

### What remains unverified
1. **PCA9685 register read-back** — I2C writes are sent without errors, but whether values actually stick in PCA9685 registers has not been confirmed
2. **Schematic mapping** — exact PCA9685 channel → TB6612FNG pin wiring on JETANK expansion board remains unknown (no official schematic available)
3. **STBY pin** — TB6612FNG has a standby pin that must be HIGH for the H-bridge to operate; whether it is hardwired HIGH or controlled by an untried PCA9685 channel is unknown
4. **VM voltage** — whether TB6612FNG's motor supply pin (VM) is actually receiving 12V from the battery rail through the expansion board traces

### Alternatives to explore for resolution
- Read back PCA9685 registers after writes via `i2cget` to confirm register values stick
- Probe TB6612FNG pins (VM, STBY, IN1, IN2, PWMA/B) directly with a multimeter while motion commands are active
- Cross-reference `waveshare/JETANK` GitHub repo for expansion board schematic or pinout documentation
- Test motors by wiring directly to the battery to rule out hardware damage

---

## 12. Repository Layout & Docker Workflow

### Directory structure on Jetson
```
~/jetbot/                  — Original NVIDIA JetBot repo (JP4.5 era, Python-based)
~/jetbot-orin/             — moatazsawi/jetbot-orin (Orin-adapted, Docker-based)
~/jetbot_waveshare/        — Waveshare adaptation (what JupyterLab actually imports)
~/JETANK/                  — waveshare/JETANK (servo install, calibration scripts)
```

### Docker-based ML workflow
Reference [moatazsawi/jetbot-orin](https://github.com/moatazsawi/jetbot-orin):
```bash
sudo docker pull moatazsawi/jetbot-orin-ml:36.4.0
sudo docker pull moatazsawi/jetbot-orin-display:36.4.0
./scripts/run-ml.sh        # Starts JupyterLab at http://<jetson_ip>:8888
./scripts/run-display.sh   # OLED display container
```

### Key constraint
ML work runs inside Docker containers, not via local pip. JupyterLab is accessed through the browser, not run locally on the Jetson desktop.

### Docker/jupyter not yet set up
As of the latest session, Docker images have not yet been pulled on the current JetPack 6.2 install. The team has been focused on hardware bring-up (power, WiFi, camera, servos). Docker setup is the next dependency for running the AI notebook stack (road following, object detection, autonomous navigation).

Planned images:
```bash
sudo docker pull moatazsawi/jetbot-orin-ml:36.4.0
sudo docker pull moatazsawi/jetbot-orin-display:36.4.0
```

---

## Summary of Critical Blockers

| # | Blocker | Status | Impact |
|---|---------|--------|--------|
| 1 | JETANK board cannot power Jetson Orin Nano | Unresolved | Blocks all tasks — need Veger T100 + PD trigger cable |
| 2 | Drive motors not responding | Unresolved | Blocking Task A control — likely wiring/schematic gap |
| 3 | Camera fusion pipeline | Not started | Tasks B, A blocked by #1 and #2 |
| 4 | Storage (83% full / 28 GiB total) | Monitoring | May block Docker image pulls |

---

## Cross-Cutting: Package & Dependency Management

Several install issues shared a common root cause: **JetPack 6.2 SD card image is stripped down** compared to a standard Ubuntu 22.04 install. Missing or broken out of the box:

- `pip3` not in root's PATH — must use `sudo python3 -m pip` instead of `sudo pip3`
- `python3-setuptools` not installed — required before running JETANK `install.sh`
- `apt-news.service` and `esm-cache.service` missing — harmless, install script warns but continues
- `/etc/apt/sources.list` duplicate entries from install script appending without checking — warnings only
- `//workspace/jetbot/notebooks` path doesn't exist — install script tries to copy notebooks there but the parent path is missing on bare JP6.2

---

## Resolved Issues

| # | Issue | Solution | Blocker for driving? |
|---|-------|----------|----------------------|
| 1 | Wrong OS (JP4.x/5.x) for Orin hardware | JetPack 6.2 SD card image | Yes — resolved |
| 2 | No WiFi (iwlwifi missing from kernel) | `backport-iwlwifi-dkms` | Yes — resolved |
| 3 | GDM3 binary missing | `apt install --reinstall gdm3` | No |
| 4 | pip broken via apt | `curl https://bootstrap.pypa.io/get-pip.py | python3` | No |
| 5 | Camera not detected (no /dev/video0) | IMX219 device tree overlay in extlinux.conf | No |
| 6 | OLED stats.py wrong I2C bus, interface, imports | Rewrote with luma.oled, bus 7, wlP1p1s0 | No |
| 7 | ServoInit centres drifted | Updated values in both TTLServo.py files | No |
| 8 | servoInt.py missing `import time` | `sed -i '3a import time'` | No |
| 9 | PCA9685 set_pwm(0,0) = FULL_ON (brake mode) | Changed to set_pwm(0, 4096) for FULL_OFF | **Yes — critical** (fix applied, motors still not moving) |
| 10 | Motor channel mapping wrong for Waveshare | Updated to Waveshare PCA9685 channel layout | **Yes — critical** (fix applied, motors still not moving) |
