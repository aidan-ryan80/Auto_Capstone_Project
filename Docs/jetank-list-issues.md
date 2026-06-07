# JETANK AI Robot — Issues, Solutions & Future Work

---

## 1. WiFi Connectivity

**Problem:** No wireless network interface available after flashing JetPack 6.2.

**Root cause:** JetPack 6.x ships with a stripped-down kernel that omits the `iwlwifi` module required for the onboard Intel Wireless 8265/8275 card. The card is physically present and detected on the PCIe bus but produces no network interface.

**Current solution:** Installed `backport-iwlwifi-dkms` over a temporary Ethernet connection. The package compiles and installs the `iwlwifi` module against the running kernel via DKMS. The wireless interface `wlP1p1s0` now appears on every boot automatically.

**Alternatives considered:**
- USB WiFi dongle with a supported chipset (Realtek RTL8812AU or MediaTek MT7612U)
- Travel router in client-bridge mode connected via Ethernet (carries the router on the chassis)
- Phone USB tethering

**Future:** No further action needed. DKMS ensures the driver survives kernel updates.

---

## 2. Power Architecture Mismatch

**Problem:** The JETANK expansion board cannot power the Jetson Orin Nano. The robot runs untethered on batteries for motors but still requires a wall plug for the Jetson.

**Root cause:** The JETANK was designed for the Jetson Nano, which accepts 5V via the GPIO header. The Orin Nano requires 9–20V via a DC barrel jack and does not accept power through GPIO. The expansion board's APW7313 regulator outputs 5V — useless for the Orin Nano.

**Current solution:** Split power paths. The Jetson Orin Nano is powered separately via a Veger T100 100W power bank using a USB-C PD trigger cable set to 15V with a 5.5×2.5mm barrel plug. The JETANK's 18650 batteries continue to power the motors and servos independently. The two rails share only a common ground through the GPIO header.

**Important note:** USB-A to USB-C bypasses Power Delivery entirely — must use USB-C to USB-C between the T100 and the trigger cable. The trigger cable must be set to 15V or 20V (not 5V or 9V) for the Jetson to boot.

**Alternatives considered:**
- 3S LiPo battery (11.1–12.6V) with correct barrel connector directly powering the Jetson
- 19V laptop-style portable power bank
- Waveshare UPS Module (C) designed specifically for Jetson Orin with 21700 cells

**Future:** Mount the Veger T100 on the JETANK chassis using velcro or a 3D-printed bracket, positioned low and centred for balance. Verify the full wireless+battery configuration before autonomous driving tests.

---

## 3. Camera Not Detected

**Problem:** No `/dev/video*` device appeared after connecting the IMX219-160 camera. `dmesg` showed "driver not enabled, cannot register any devices" four times.

**Root cause:** The IMX219 sensor driver is not built as a loadable kernel module on JetPack 6.2 — it is activated via a device tree overlay. Without the overlay referenced in `extlinux.conf`, the kernel never loads the driver and no video device is created. The VI (Video Input) hardware initialises correctly but finds no configured sensor.

**Current solution:** Added the IMX219 device tree overlay to `/boot/extlinux/extlinux.conf`:
- `FDT /boot/tegra234-p3768-0000+p3767-0005-nv-super.dtb`
- `OVERLAYS /boot/tegra234-p3767-camera-p3768-imx219-A.dtbo`

After reboot, `/dev/video0` appeared and a GStreamer snapshot test confirmed a working feed via `nvarguscamerasrc`.

**Alternatives considered:**
- USB camera (bypasses CSI/overlay requirement entirely)
- Switching to CAM1 port using the `-C` overlay variant

**Future:** Test camera feed within JupyterLab notebooks. Integrate with the object detection and autonomous navigation pipelines.

---

## 4. OLED Display Not Initialising

**Problem:** The onboard 128×32 OLED display remained blank on boot.

**Root cause:** Three compounding issues in the original `stats.py` from the JetBot repo:
1. Required `qwiic` and `Adafruit_SSD1306` libraries — neither installed on JetPack 6.2
2. Hardcoded I2C bus 1 — the JETANK expansion board uses bus 7
3. Checked for interface `wlan0` — the Orin Nano uses `wlP1p1s0`

Additionally, no systemd service existed to auto-start the display script on boot.

**Current solution:** Rewrote `stats.py` from scratch using `luma.oled` and `psutil`. Configured for I2C bus 7 at address `0x3C`, DejaVuSans 7pt font, and correct interface names. The script alternates every 10 seconds between a system stats page (IP, CPU, RAM, disk) and a component status page (WiFi, camera, OLED, PCA9685, INA219, servos 1 and 5). Deployed as a `systemd` service (`jetbot_stats.service`) that starts automatically on boot.

**Alternatives considered:**
- Running the original stats.py after installing qwiic and Adafruit libraries (rejected — outdated dependencies)

**Future:** Update the component status page as more hardware comes online (servos 2–4, drive motors).

---

## 5. Servo Calibration & Control

**Problem:** Running `servoAngleCtrl` commands caused servos to spin aggressively to wrong positions, tangling the base rotation cable. Physical manipulation was needed to free the chassis.

**Root cause:** Two issues:
1. `servoInit` in `TTLServo.py` defaulted to position 512 (centre) for all servos, but the physical centre of the mounted servos corresponded to different encoder values (1021 for servo 1, 811 for servo 5) after assembly.
2. `servoInt.py` used `time.sleep()` without importing the `time` module, causing a silent crash after port initialisation.

**Current solution:**
- Fixed the missing `import time` in `servoInt.py`
- Updated `servoInit` to `[None, 1021, 512, 512, 512, 811]` in both the source repo file and the installed package file after reading back actual centre positions via a serial bus scan
- Confirmed all 5 servo IDs (1–5) pre-assigned and responding correctly on `/dev/ttyTHS1` at 1,000,000 baud

**Alternatives considered:**
- Re-flashing servo EEPROM with new centre positions (overkill — software calibration sufficient)

**Future:**
- Assemble robotic arm (servos 2, 3, 4) and re-run calibration for those axes
- Update `servoInit` values accordingly
- Add software angle limits for servo 1 (±80° max) to prevent cable tangling — no physical stop exists

---

## 6. Drive Motors Not Responding (In Progress)

**Problem:** `robot.forward()`, `robot.left()` and all other drive commands execute without errors but produce zero physical movement in the tank thread motors.

**Root cause (partially identified):** Two bugs found in the `jetbot_waveshare` package:
1. `pca9685.py` `set_pin(channel, 0)` used `set_pwm(channel, 0, 0)`. Per PCA9685 datasheet, when ON=OFF=0, ON has priority — the pin is forced always HIGH instead of LOW. This means the direction pin IN2 was never pulled low, putting the TB6612FNG in brake mode permanently regardless of PWM.
2. `motor.py` used the Adafruit MotorHAT channel layout (`Motor 1: PWM=ch2, IN1=ch3, IN2=ch4`) instead of the Waveshare standard (`PWMA=ch0, AIN1=ch1, AIN2=ch2`).

Both bugs were fixed. Root cause of remaining no-movement behaviour is still under investigation.

**What has been ruled out:**
- PCA9685 not present — confirmed at address 0x60 on I2C bus 7 ✓
- Power to expansion board — 11.85V (79%) confirmed via INA219 ✓
- Motor physical connections — motors verified plugged into correct terminals ✓
- Python import path — confirmed JupyterLab imports from `jetbot_waveshare` ✓
- PCA9685 not receiving commands — no I2C errors thrown ✓

**What has not yet been verified:**
- PCA9685 register read-back (writes confirmed sent but not confirmed sticking)
- Exact JETANK expansion board schematic — precise PCA9685 channel to TB6612FNG pin wiring
- Whether TB6612FNG STBY pin is hardwired or requires explicit activation
- Whether TB6612FNG VM pin (motor supply voltage) is correctly receiving 12V from battery rail

**Current status:** Handed to Claude Code for deeper investigation — comparing `waveshare/JETANK` hardware documentation with the `jetbot_waveshare` motor implementation.

**Alternatives to explore:**
- Read back PCA9685 registers after writes to confirm communication
- Probe TB6612FNG pins directly with a multimeter while commands are sent
- Check the JETANK expansion board schematic for exact channel mapping
- Test motors by temporarily wiring them directly to the battery to rule out hardware damage

**Future:** Once resolved, test basic motion notebooks (`basic_motion.ipynb`) in JupyterLab, then proceed to autonomous navigation development.

---

## 7. JupyterLab / Docker Environment

**Problem (pending):** The `jetbot-orin` repository uses Docker containers for JupyterLab and the ML environment. Docker has not yet been set up on the current JetPack 6.2 image.

**Root cause:** The team has been focused on hardware bring-up. Docker setup is a prerequisite for running the full AI notebook stack.

**Future:**
- Follow the `moatazsawi/jetbot-orin` setup guide to pull the Docker images
- Launch JupyterLab container with GPU access
- Run the provided notebooks for basic motion, road following, and object detection

---

## 8. Package & Dependency Management

**Problem:** Several installation issues encountered due to JetPack 6.2 being a stripped-down image without standard tools.

**Root cause:** JetPack 6.2 SD card image does not include `pip3` in PATH for root, `python3-setuptools`, or several system services (`apt-news.service`, `esm-cache.service`) that `install.sh` expects.

**Current solution:**
- Installed `python3-setuptools` before running `install.sh`
- Used `sudo python3 -m pip install` instead of `sudo pip3` for system-wide package installation
- Duplicate entries in `/etc/apt/sources.list` (lines 43/44) identified — warnings only, do not affect functionality

**Future:** Document the correct installation sequence in project README so future teammates can reproduce the environment cleanly on a fresh flash.

---

## Summary Table

| # | Issue | Status | Blocker for driving? |
|---|-------|--------|----------------------|
| 1 | WiFi driver missing | ✅ Resolved | Yes — resolved |
| 2 | Power architecture mismatch | ✅ Resolved (partial) | Yes — Jetson runs on wall power, battery untested |
| 3 | Camera not detected | ✅ Resolved | No |
| 4 | OLED display blank | ✅ Resolved | No |
| 5 | Servo calibration | ✅ Resolved | No |
| 6 | Drive motors not responding | 🔄 In progress | **Yes — critical** |
| 7 | JupyterLab / Docker setup | ⏳ Pending | Yes — needed for notebooks |
| 8 | Package management | ✅ Resolved | No |
