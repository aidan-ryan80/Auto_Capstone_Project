# JETANK AI Kit — Full Project Session Notes

**Hardware:** Waveshare JETANK AI Kit with Jetson Orin Nano Super  
**OS:** JetPack 6.2 (kernel `5.15.148-tegra`, Ubuntu 22.04)  
**Reference repositories:**
- [moatazsawi/jetbot-orin](https://github.com/moatazsawi/jetbot-orin) — JupyterLab notebooks for motion control
- [waveshare/JETANK](https://github.com/waveshare/JETANK) — Servo/motor installation scripts

---

## 1. Background & Context

The team flashed **JetPack 6.2 for Jetson Orin Nano** instead of the original JetPack image for Jetson Nano, due to hardware compatibility requirements. Most existing guides and the JETANK repo itself target the older Jetson Nano, so many things required adaptation.

**Key hardware identifiers:**
- Ethernet interface: `enP8p1s0`
- WiFi interface: `wlP1p1s0` *(not `wlan0` — JetPack 6.x uses predictable interface naming)*
- Hostname: `jetbot-orin-nano`
- User: `jetbot-04`
- Serial port for servos: `/dev/ttyTHS1`
- I2C bus for expansion board: bus **7**
- Camera: **IMX219-160** (CSI, connected to **CAM0**)
- Board identified as: `NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super`

---

## 2. WiFi Setup

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
- WiFi interface: `wlP1p1s0`
- The `backport-iwlwifi-dkms` module persists across reboots and kernel updates via DKMS
- Ethernet cable can be unplugged — board runs fully wireless

---

## 3. JetPack 6.2 Image — Reflashing Reference

**Kernel produced:** `5.15.148-tegra`  
**Direct download link:**
```
https://developer.nvidia.com/downloads/embedded/l4t/r36_release_v4.3/jp62-orin-nano-sd-card-image.zip
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

---

## 4. Power Architecture

### Original design (Jetson Nano — NOT applicable to Orin Nano)
```
18650 Batteries (3S, ~12.6V)
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
- The OLED display, INA219 current sensor, and PCA9685 PWM controller (all I2C, all 5V) are powered by the Jetson whenever the Jetson is on
- The expansion board switch only controls the 12.6V motor/servo rail
- This is by design and safe — the two voltage rails are isolated by hardware

### Power-on sequence
**Always power the expansion board first, then the Jetson Orin Nano.**  
Reason: The Jetson initialises I2C and serial buses on boot. If the expansion board is unpowered, bus lines float and devices may not be detected until reboot.

### Battery connection — critical note
**Must use USB-C to USB-C** between the Veger T100 and the PD trigger cable. USB-A to USB-C bypasses Power Delivery entirely — the bank falls back to 5V and the Jetson will not power on. Set trigger cable to **15V**.

### Veger T100 specs
- Outputs: 5V/9V/12V/15V/20V via USB-C PD (max 100W)
- Estimated runtime at ~10–12W load: 4–5 hours
- Barrel plug required: **5.5mm OD × 2.5mm ID, center positive**

---

## 5. JETANK Software Installation

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
- `apt-news.service` and `esm-cache.service` not found — harmless, ignore
- Duplicate entries in `/etc/apt/sources.list` (lines 43/44) — warnings only, clean up with `sudo nano /etc/apt/sources.list` if desired
- `cp: cannot create directory '//workspace/jetbot/notebooks'` — harmless, notebooks path doesn't exist on bare JetPack 6.2 image but does not affect servo functionality
- Setuptools deprecation warnings — harmless

---

## 6. Servo Calibration & Motor Control

### Hardware
- **Servo type:** Feetech SCS15-AP serial bus servos
- **Protocol:** SCS (protocol_end = 1)
- **Baudrate:** 1,000,000
- **Serial port:** `/dev/ttyTHS1`
- **Servo IDs:** 1–5 (pre-programmed by colleagues, persistent in EEPROM)
- **Current configuration:** Servos 1 and 5 mounted (camera mount, no gripper assembled yet)
- **Daisy-chained** in series

### Servo scan — confirm all servos are alive
```bash
python3 - <<'EOF'
from SCSCtrl.scservo_sdk import *
portHandler = PortHandler('/dev/ttyTHS1')
packetHandler = PacketHandler(1)
portHandler.openPort()
portHandler.setBaudRate(1000000)

print("Scanning IDs 1-10...")
for i in range(1, 11):
    pos, result, error = packetHandler.read4ByteTxRx(portHandler, i, 56)
    if result == COMM_SUCCESS:
        print(f"  Found servo at ID {i}, position {SCS_LOWORD(pos)}")
    else:
        print(f"  No response from ID {i}")

portHandler.closePort()
EOF
```

**Confirmed scan result:** IDs 1–5 all respond.

### servoInit calibration values — IMPORTANT
After physical manipulation during testing, the servos' actual centre positions drifted from the default 512. Updated values confirmed by visual inspection:

```python
servoInit = [None, 1021, 512, 512, 512, 811]
```

This must be updated in **two files**:
```bash
vim /home/jetbot-04/.local/lib/python3.10/site-packages/SCSCtrl/TTLServo.py  # active import
vim /home/jetbot-04/JETANK/SCSCtrl/TTLServo.py                                # source repo
```

### Safe motion commands for current config (IDs 1 and 5 only)
```python
import time
from SCSCtrl import TTLServo

# Always use low speed (30) first when testing after reassembly
TTLServo.servoAngleCtrl(1, 0, 1, 30)   # base rotation to centre
time.sleep(3)
TTLServo.servoAngleCtrl(5, 0, 1, 30)   # camera tilt to centre
```

⚠️ **Never command servo ID 1 more than ±80 degrees from centre** — it has no physical stop and will tangle cables.  
⚠️ **Always use speed 30 when testing after any physical reassembly** — use 150 only once motion is confirmed safe.

### Move all servos test
```bash
python3 - <<'EOF'
import time
from SCSCtrl.scservo_sdk import *

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
The main calibration script `~/JETANK/servoInt.py` uses `time.sleep()` but `import time` was missing. Fix:
```bash
sed -i '3a import time' ~/JETANK/servoInt.py
```

---

## 7. I2C Bus & Expansion Board Devices

**Bus:** 7 (confirmed via `sudo i2cdetect -y -r 7`)

| Address | Device | Status |
|---------|--------|--------|
| `0x3c` | SSD1306 OLED display | ✅ Present |
| `0x41` | INA219 current sensor | ✅ Present |
| `0x60` | PCA9685 PWM controller | ✅ Present |
| `0x70` | PCA9685 (broadcast) | ✅ Present |

---

## 8. OLED Display Setup

### Dependencies
```bash
sudo python3 -m pip install luma.oled psutil
```

*(Must use `sudo python3 -m pip` — `pip3` is not in root's PATH on this image)*

### Stats script location
```
~/jetbot/jetbot/apps/stats.py
```

The original `stats.py` from the jetbot repo had three problems:
1. Hardcoded `i2c_bus=1` — should be **7**
2. Checked for `wlan0` — should be **`wlP1p1s0`**
3. Required `qwiic` and `Adafruit_SSD1306` — not installed, replaced with `luma.oled`

### Current script features
- **Page 1 (10s):** WiFi IP, CPU usage, Memory usage, Disk usage
- **Page 2 (10s):** Component status — WiFi, Camera, OLED, PCA9685, INA219, Servo 1, Servo 5
- Font: DejaVuSans 7pt (fits 4 lines on 128×32 display without overlap)
- I2C bus: 7, address: 0x3C

### Systemd service
Service file: `/etc/systemd/system/jetbot_stats.service`

Key fix — `ExecStart` must call the script directly, not via `-m` module syntax:
```ini
[Unit]
Description=JetBot stats display service

[Service]
Type=simple
User=jetbot-04
ExecStart=/usr/bin/python3 /home/jetbot-04/jetbot/jetbot/apps/stats.py
WorkingDirectory=/home/jetbot-04
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable jetbot_stats.service
sudo systemctl start jetbot_stats.service
sudo systemctl status jetbot_stats.service
```

**Status: Running and enabled on boot ✅**

---

## 9. Camera Setup (IMX219-160)

### Hardware
- **Sensor:** IMX219-160
- **Interface:** CSI ribbon cable (FFC)
- **Connected to:** CAM0 (port A) on the Jetson Orin Nano module
- **I2C address:** 0x10 on bus 9

### CSI connector notes
The CSI ZIF connector on the Jetson module is extremely fragile:
- Lift the locking latch **upward** before inserting (1–2mm, use fingernail or plastic spudger only)
- Insert cable with **metal contacts facing down**
- Press latch back down until flat
- Never use metal tools near the latch

### Root cause of camera not working
The IMX219 kernel module is **not built as a loadable module** on JetPack 6.2 — it is activated via device tree overlay. Without the overlay in `extlinux.conf`, the driver never loads and no `/dev/video*` devices are created. The dmesg message `driver not enabled, cannot register any devices` confirms this.

### Fix — add IMX219 overlay to extlinux.conf
```bash
sudo vim /boot/extlinux/extlinux.conf
```

Updated `LABEL primary` section:
```
LABEL primary
      MENU LABEL primary kernel
      LINUX /boot/Image
      INITRD /boot/initrd
      FDT /boot/tegra234-p3768-0000+p3767-0005-nv-super.dtb
      OVERLAYS /boot/tegra234-p3767-camera-p3768-imx219-A.dtbo
      APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 mminit_loglevel=4 console=ttyTCU0,115200 firmware_class.path=/etc/firmware fbcon=map:0 video=efifb:off console=tty0
```

- `-A` overlay = CAM0 (use this for JETANK — notebooks use `sensor-id=0`)
- `-C` overlay = CAM1 (only if cable is moved to CAM1)

```bash
sudo reboot
```

### Verify after reboot
```bash
ls /dev/video*
sudo dmesg | grep -i "imx219\|video\|csi"
```

### Test video feed
```bash
# Snapshot test (no display required)
gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! \
'video/x-raw(memory:NVMM),width=1280,height=720' ! \
nvvidconv ! jpegenc ! filesink location=~/test_snap.jpg

# Copy to PC to view
scp jetbot-04@192.168.x.xxx:~/test_snap.jpg .
```

---

## 10. Networking Reference

| Item | Value |
|------|-------|
| Hostname | `jetbot-orin-nano` |
| SSH user | `jetbot-04` |
| Ethernet interface | `enP8p1s0` |
| WiFi interface | `wlP1p1s0` |
| Find IP via nmap | `nmap -sn 192.168.x.0/24` |
| mDNS (may not work) | `ssh jetbot-04@jetbot-orin-nano.local` |

---

## 11. Claude Code — Removed

Claude Code was installed on the JETANK by a colleague but removed during this session since the associated account had no active subscription. Removal commands:

```bash
rm ~/.local/bin/claude
rm -rf ~/.local/share/claude
rm -rf ~/.claude
rm -rf ~/.claude.json
rm -rf ~/.config/claude
```

---

## 12. Next Steps

- [x] Reboot after adding IMX219 overlay to extlinux.conf and verify `/dev/video0` appears ✅
- [x] Test camera snapshot with GStreamer pipeline ✅
- [ ] Test USB-C to USB-C connection from Veger T100 at 15V to power Jetson wirelessly
- [ ] Verify motors move when expansion board is battery-powered and Jetson is on Veger T100
- [ ] Follow [jetbot-orin](https://github.com/moatazsawi/jetbot-orin) setup guide to pull Docker images and launch JupyterLab
- [ ] Test basic motion notebooks from JupyterLab (JETANK_1_servos_en.ipynb confirmed working with updated servoInit values)
- [ ] Assemble remaining robotic arm (servos 2, 3, 4) and update servoInit accordingly
- [ ] Mount Veger T100 onto JETANK chassis (velcro or 3D printed bracket, mount low and centred)

---

## 13. Drive Motor Investigation (IN PROGRESS — not yet resolved)

### Hardware
- **Motor driver chip:** TB6612FNG dual H-bridge on JETANK expansion board
- **PWM controller:** PCA9685 at I2C address `0x60` on bus **7** (confirmed present)
- **Motor terminals:** Left and right tank thread motors physically connected to expansion board output terminals
- **Power:** 18650 batteries at 11.85V (79%), switch ON, charger connected

### Software stack confirmed
- `from jetbot import Robot` in JupyterLab resolves to `/home/jetbot-04/jetbot_waveshare/jetbot/robot.py` ✅
- `robot.py` uses `PCA9685(address=0x60, bus=7)` — correct for this hardware ✅
- `Robot()` instantiates without errors ✅
- All `robot.forward()`, `robot.left()` etc. commands run without errors ✅
- **But motors produce zero physical movement** ❌

### Directories on the system
```
~/jetbot/           — original NVIDIA JetBot repo (NOT jetbot-orin)
~/jetbot-orin/      — moatazsawi/jetbot-orin repo (Docker-based, no Python motor files)
~/jetbot_waveshare/ — Waveshare adaptation (what JupyterLab actually imports)
~/JETANK/           — waveshare/JETANK repo (servo control, install scripts)
```

### Key files
```
~/jetbot_waveshare/jetbot/robot.py    — Robot class (i2c_bus=7, address=0x60)
~/jetbot_waveshare/jetbot/motor.py    — Motor class (channel mapping)
~/jetbot_waveshare/jetbot/pca9685.py  — PCA9685 driver (smbus2-based)
```

### Fixes already applied
**Fix 1 — pca9685.py set_pin(0) bug:**
The original code used `set_pwm(channel, 0, 0)` for value=0. Per PCA9685 datasheet, when ON=OFF=0, ON has priority → pin is forced always HIGH. This means IN2 was never being pulled LOW, putting TB6612FNG in brake mode. Fixed to:
```python
if value == 0:
    self.set_pwm(channel, 0, 4096)  # FULL_OFF bit — was (0,0) which is FULL ON
```

**Fix 2 — motor.py channel mapping updated to Waveshare standard:**
```python
_MOTOR_CHANNELS = {
    1: (0, 1, 2),   # PWMA=0, AIN1=1, AIN2=2  (left motor)
    2: (5, 3, 4),   # PWMB=5, BIN1=3, BIN2=4  (right motor)
    3: (10, 9, 8),
    4: (13, 12, 11),
}
```
Original was Adafruit MotorHAT layout: `1: (2,3,4)` and `2: (7,6,5)` — wrong for Waveshare hardware.

**Neither fix produced motor movement.**

### Brute force scan performed
Tried all common PCA9685 channel triplets with correct FULL_OFF logic and STBY channels 8,9,12,13,14,15 set HIGH — no movement on any combination.

### What has NOT been verified yet
- Whether PCA9685 register writes are actually sticking (read-back verification)
- Exact schematic mapping of PCA9685 channels → TB6612FNG pins on the JETANK expansion board
- Whether TB6612FNG STBY pin is hardwired or controlled by a PCA9685 channel not yet tried
- Whether TB6612FNG VM pin is actually receiving the 12V motor supply

### Recommended next step for Claude Code
Compare `waveshare/JETANK` GitHub repo and `jetbot_waveshare` local package to find the correct PCA9685 channel → TB6612FNG wiring for the JETANK expansion board. Read back PCA9685 registers after writes to confirm communication. Cross-reference with JETANK expansion board schematic if available.
