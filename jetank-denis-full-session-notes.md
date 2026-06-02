# JETANK AI Kit — Full Project Session Notes

**Hardware:** Waveshare JETANK AI Kit with Jetson Orin Nano  
**OS:** JetPack 6.2 (kernel `5.15.148-tegra`, Ubuntu 22.04)  
**Reference repositories:**

* [moatazsawi/jetbot-orin](https://github.com/moatazsawi/jetbot-orin) — JupyterLab notebooks for motion control
* [waveshare/JETANK](https://github.com/waveshare/JETANK) — Servo/motor installation scripts

\---

## 1\. Background \& Context

The team flashed **JetPack 6.2 for Jetson Orin Nano** instead of the original JetPack image for Jetson Nano, due to hardware compatibility requirements. Most existing guides and the JETANK repo itself target the older Jetson Nano, so many things required adaptation.

**Key hardware identifiers:**

* Ethernet interface: `enP8p1s0`
* WiFi interface: `wlP1p1s0` *(not `wlan0` — JetPack 6.x uses predictable interface naming)*
* Hostname: `jetbot-orin-nano`
* User: `jetbot-04`
* Serial port for servos: `/dev/ttyTHS1`
* I2C bus for expansion board: bus **7**

\---

## 2\. WiFi Setup

### Root Cause

JetPack 6.x ships with a stripped-down kernel missing the `iwlwifi` module required for the onboard **Intel Wireless 8265/8275** card. The card was physically present and detected on the PCIe bus but produced no wireless interface.

**Diagnosis commands used:**

```bash
uname -r
# 5.15.148-tegra

lspci | grep -i -E "network|wireless|wifi"
# 0001:01:00.0 Network controller: Intel Corporation Wireless 8265 / 8275 (rev 78)

modinfo iwlwifi
# modinfo: ERROR: Module iwlwifi not found.

ip link show
# No wlan interface present
```

### Fix

With Ethernet connected, install the backported Intel WiFi driver:

```bash
sudo apt update
sudo apt install -y backport-iwlwifi-dkms
sudo reboot
```

After reboot the interface `wlP1p1s0` appeared. Connect to WiFi:

```bash
sudo nmcli dev wifi connect "SSID" password "password"
```

Plain `nmcli` without `sudo` returns "Not authorized to control networking" — always use `sudo`.

### Result

* WiFi interface: `wlP1p1s0`
* The `backport-iwlwifi-dkms` module persists across reboots and kernel updates via DKMS
* Ethernet cable can be unplugged — board runs fully wireless

\---

## 3\. JetPack 6.2 Image — Reflashing Reference

**Kernel produced:** `5.15.148-tegra`  
**Direct download link:**

```
https://developer.nvidia.com/downloads/embedded/l4t/r36\_release\_v4.3/jp62-orin-nano-sd-card-image.zip
```

**Flash tool:** Balena Etcher (not Rufus — Rufus cannot handle raw Linux partition images)

**SD card prep on Windows 11 (Diskpart):**

```
diskpart
list disk
select disk X      ← your SD card number
clean
create partition primary
format fs=exfat quick label="SDCARD"
assign letter=E
exit
```

**After flashing:** Re-apply the WiFi driver fix (Section 2) on first boot. QSPI firmware update is NOT needed when coming from an existing JetPack 6.x install.

\---

## 4\. Power Architecture

### Original design (Jetson Nano — NOT applicable to Orin Nano)

```
18650 Batteries (3S, \~12.6V)
        ↓
JETANK Expansion Board
        ↓ (APW7313 regulator → 5V)
Jetson Nano (via GPIO header)
```

### Your actual architecture (Jetson Orin Nano)

The Orin Nano requires **9–20V via DC barrel jack** and does NOT accept 5V via GPIO. The two boards must be powered independently:

```
Path 1: Veger T100 power bank
        ↓ (USB-C to USB-C — PD trigger cable set to 15V)
        ↓ (5.5×2.5mm barrel plug)
Jetson Orin Nano DC barrel jack

Path 2: JETANK 18650 batteries + expansion board switch
        ↓
Motors, servos, TB6612FNG motor driver, SY8286 servo regulator
```

### Important behaviour — GPIO 5V backfeed

The Jetson's GPIO header pins 2 and 4 are always live (5V) the moment the Jetson is powered — regardless of the expansion board's switch state. This means:

* The OLED display, INA219 current sensor, and PCA9685 PWM controller (all I2C, all 5V) are powered by the Jetson whenever the Jetson is on
* The expansion board switch only controls the 12.6V motor/servo rail
* This is by design and safe — the two voltage rails are isolated by hardware

### Power-on sequence

**Always power the expansion board first, then the Jetson Orin Nano.**  
Reason: The Jetson initialises I2C and serial buses on boot. If the expansion board is unpowered, bus lines float and devices may not be detected until reboot.

### Battery connection — critical note

**Must use USB-C to USB-C** between the Veger T100 and the PD trigger cable. USB-A to USB-C bypasses Power Delivery entirely — the bank falls back to 5V and the Jetson will not power on. Set trigger cable to **15V**.

### Veger T100 specs

* Outputs: 5V/9V/12V/15V/20V via USB-C PD (max 100W)
* Estimated runtime at \~10–12W load: 4–5 hours
* Barrel plug required: **5.5mm OD × 2.5mm ID, center positive**

\---

## 5\. JETANK Software Installation

### Install sequence

```bash
cd JETANK/
sudo chmod +x config.sh install.sh
sudo ./config.sh jetbot     # reboots the system — SSH session will drop, this is normal
```

After reboot:

```bash
cd JETANK/
sudo apt install -y python3-setuptools   # required before install.sh
sudo ./install.sh
```

### Known install.sh issues on JetPack 6.2

* `apt-news.service` and `esm-cache.service` not found — harmless, ignore
* Duplicate entries in `/etc/apt/sources.list` (lines 43/44) — warnings only, clean up with `sudo nano /etc/apt/sources.list` if desired
* `cp: cannot create directory '//workspace/jetbot/notebooks'` — harmless, notebooks path doesn't exist on bare JetPack 6.2 image but does not affect servo functionality
* Setuptools deprecation warnings — harmless

\---

## 6\. Servo Calibration \& Motor Control

### Hardware

* **Servo type:** Feetech SCS15-AP serial bus servos
* **Protocol:** SCS (protocol\_end = 1)
* **Baudrate:** 1,000,000
* **Serial port:** `/dev/ttyTHS1`
* **Servo IDs:** 1–5 (pre-programmed by colleagues, persistent in EEPROM)
* **Current configuration:** Servos 1 and 5 mounted (camera mount, no gripper)
* **Daisy-chained** in series

### Servo scan — confirm all servos are alive

```bash
python3 - <<'EOF'
from SCSCtrl.scservo\_sdk import \*
portHandler = PortHandler('/dev/ttyTHS1')
packetHandler = PacketHandler(1)
portHandler.openPort()
portHandler.setBaudRate(1000000)

print("Scanning IDs 1-10...")
for i in range(1, 11):
    pos, result, error = packetHandler.read4ByteTxRx(portHandler, i, 56)
    if result == COMM\_SUCCESS:
        print(f"  Found servo at ID {i}, position {SCS\_LOWORD(pos)}")
    else:
        print(f"  No response from ID {i}")

portHandler.closePort()
EOF
```

**Confirmed scan result:** IDs 1–5 all respond, all near position 512 (centre/home).

### Move all servos test

```bash
python3 - <<'EOF'
import time
from SCSCtrl.scservo\_sdk import \*

portHandler = PortHandler('/dev/ttyTHS1')
packetHandler = PacketHandler(1)
portHandler.openPort()
portHandler.setBaudRate(1000000)

print("Moving all servos to position 700...")
for i in range(1, 6):
    packetHandler.write2ByteTxRx(portHandler, i, 46, 150)
    packetHandler.write2ByteTxRx(portHandler, i, 42, 700)

time.sleep(3)

print("Moving all servos back to centre...")
for i in range(1, 6):
    packetHandler.write2ByteTxRx(portHandler, i, 42, 512)

time.sleep(3)
portHandler.closePort()
EOF
```

### servoInt.py note

The main calibration script `\~/JETANK/servoInt.py` uses `time.sleep()` but `import time` was missing. Fix:

```bash
sed -i '3a import time' \~/JETANK/servoInt.py
```

Servos were already calibrated by colleagues — positions \~512 at rest confirms they are at home position. Calibration does not need to be repeated.

\---

## 7\. I2C Bus \& Expansion Board Devices

**Bus:** 7 (confirmed via `sudo i2cdetect -y -r 7`)

|Address|Device|Status|
|-|-|-|
|`0x3c`|SSD1306 OLED display|✅ Present|
|`0x41`|INA219 current sensor|✅ Present|
|`0x60`|PCA9685 PWM controller|✅ Present|
|`0x70`|PCA9685 (broadcast)|✅ Present|

\---

## 8\. OLED Display Setup

### Dependencies

```bash
sudo python3 -m pip install luma.oled psutil
```

*(Must use `sudo python3 -m pip` — `pip3` is not in root's PATH on this image)*

### Stats script location

```
\~/jetbot/jetbot/apps/stats.py
```

The original `stats.py` from the jetbot repo had three problems:

1. Hardcoded `i2c\_bus=1` — should be **7**
2. Checked for `wlan0` — should be **`wlP1p1s0`**
3. Required `qwiic` and `Adafruit\_SSD1306` — not installed, replaced with `luma.oled`

### Current script features

* **Page 1 (10s):** WiFi IP, CPU usage, Memory usage, Disk usage
* **Page 2 (10s):** Component status — WiFi, Camera, OLED, PCA9685, INA219, Servo 1, Servo 5
* Font: DejaVuSans 7pt (fits 4 lines on 128×32 display without overlap)
* I2C bus: 7, address: 0x3C

### Systemd service

Service file: `/etc/systemd/system/jetbot\_stats.service`

Key fix — `ExecStart` must call the script directly, not via `-m` module syntax:

```ini
\[Unit]
Description=JetBot stats display service

\[Service]
Type=simple
User=jetbot-04
ExecStart=/usr/bin/python3 /home/jetbot-04/jetbot/jetbot/apps/stats.py
WorkingDirectory=/home/jetbot-04
Restart=always
RestartSec=5

\[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable jetbot\_stats.service
sudo systemctl start jetbot\_stats.service
sudo systemctl status jetbot\_stats.service
```

**Status: Running and enabled on boot ✅**

\---

## 9\. Networking Reference

|Item|Value|
|-|-|
|Hostname|`jetbot-orin-nano`|
|SSH user|`jetbot-04`|
|SSH password|`not stated`|
|Ethernet interface|`enP8p1s0`|
|WiFi interface|`wlP1p1s0`|
|Find IP via nmap|`nmap -sn 192.168.x.0/24`|
|mDNS (may not work)|`ssh jetbot-04@jetbot-orin-nano.local`|

\---

## 10\. Next Steps

* \[ ] Test USB-C to USB-C connection from Veger T100 at 15V to power Jetson wirelessly
* \[ ] Verify motors move when expansion board is battery-powered and Jetson is on Veger T100
* \[ ] Follow [jetbot-orin](https://github.com/moatazsawi/jetbot-orin) setup guide to pull Docker images and launch JupyterLab
* \[ ] Test basic motion notebooks from JupyterLab
* \[ ] Mount Veger T100 onto JETANK chassis (velcro or 3D printed bracket, mount low and centred)
* \[ ] Order USB-C PD trigger cable at correct voltage (15V, 5.5×2.5mm barrel, center positive) if barrel adapter issues persist

