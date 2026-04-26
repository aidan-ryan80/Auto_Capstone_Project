# Project Timeline

This file tracks what was **accomplished** in each work session.

---

## Session Entry Template

### Session YYYY-MM-DD
**Planned**
- 

**Accomplished**
- 

**Evidence / Notes**
- 

**Open Items / Next Session**

- 

---

### Session 2026-03-12

**Planned**

- Build the Jetson Nano Robot
- Set up the Jetpack Operating system

**Accomplished**

- Started in building the Jetson Nano Robot
- Failed in setting up the Operating system due to being stuck at boot. The OS suggesting by Tingting might be incompatible with our hardware

**Evidence / Notes**

- 

**Open Items / Next Session**

- Continue working on building the robot and setting up the Jetpack OS

---

### Session 2026-03-24

**Planned**

- Build the Jetson Nano Robot
- Set up the Jetpack Operating system

**Accomplished**

- Continued building the Robot, but don't have the batteries required. They need to be ordered
- Identified root incompatibility: legacy JetBot Nano JP4.5 images or Jetpack 4.x images are not the right target for this Orin setup.
- A Jetpack OS that is 6.0+ is necessary for Jetson Orin Nano hardware. The earlier versions are for Jetson Nano instead.

**Evidence / Notes**

- The following OS images failed with our hardware:
  - jetbot-043_nano-4gb-jp45
  - jetson-nano-jp461-sd-card-image
  - jp60dp-orin-nano-sd-card-image
  - JP512-orin-nano-sd-card-image

- The OS that worked:
  - jp62-orin-nano-sd-card-image


**Open Items / Next Session**

- Continue working on building the robot and set up wifi, ssh, and the environment on the Jetpack Operating System

---

## Session 2026-04-09

**Planned**

- Set up SSH access to the Jetson Orin Nano
- Configure WiFi connectivity
- Research hardware resources and reference implementations
- Install OS packages for development environment

**Accomplished**

- **SSH Setup**
  - Successfully installed and enabled OpenSSH server on Jetson Orin Nano.
  - Verified remote SSH access from development machine.
  - Confirmed Jetson Orin Nano is accessible at IP address on local network.

- **WiFi Troubleshooting (Initial Diagnosis)**
  - Attempted to configure WiFi connectivity.
  - Discovered **root blocker:** Intel Wireless 8265 is physically present on PCIe (confirmed via `lspci`), but `iwlwifi` kernel module is missing from JetPack 6.x kernel.
  - Diagnosed version mismatch: JetPack 6.x stripped-down kernel lacks WiFi driver support that was present in JetPack 5.x.
  - Attempted `backport-iwlwifi-dkms` install but encountered symbol version mismatches — **deferred resolution to future session**.

- **Research: jetbot-orin GitHub Repository**
  - Discovered and cloned [moatazsawi/jetbot-orin](https://github.com/moatazsawi/jetbot-orin) as reference implementation for Orin Nano + JetBot.
  - Analyzed docs and Docker containerization approach.
  - Identified this as the correct reference for Task B/C workflows (road_following, object_following notebooks).
  - Established this repo as a critical resource for understanding Orin-specific adaptations.

- **OS Package Installation & Environment Setup**
  - Installed foundational development packages and tools.
  - Set up basic system utilities for remote management and development.
  - Established baseline for Python and system libraries.

**Evidence / Notes**

- WiFi driver issue identified as a **blocking dependency** requiring kernel rebuild or driver backport.
- jetbot-orin repo structure analyzed; Docker-based ML workflow confirmed as the intended path (vs. local pip installs).
- SSH access validated as reliable fallback for remote work when WiFi is not available.
- Network blocker led to adoption of Ethernet + USB tethering as interim connectivity strategy.

**Open Items / Next Session**

- Resolve WiFi driver blocker: Either rebuild kernel with iwlwifi or apply DKMS backport patch successfully.
- Continue hardware assembly.
- Test Ethernet/tethering fallback strategy for sustained remote access.
- Begin Task C: formal assembly checklist and motor configuration.

---

## Session 2026-04-17

**Planned**
- Fix the wifi on the Jetson Orin Nano

**Accomplished**

- **WiFi Driver Fix (Denis)**
  - Diagnosed root cause: JetPack 6.x kernel lacks `iwlwifi` module despite Intel Wireless 8265 being physically present on PCIe.
  - Installed `backport-iwlwifi-dkms` package which compiled and installed the driver against the running kernel via DKMS (Dynamic Kernel Module Support).
  - After reboot, wireless interface **`wlP1s0`** came up (JetPack 6.x uses predictable naming, not `wlan0`).
  - Successfully connected to WiFi using `sudo nmcli dev wifi connect "SSID" password "password"`.
  - Verified connectivity: IP assigned, pinged 8.8.8.8 successfully, unplugged Ethernet and confirmed wireless-only operation.
  - DKMS module persists across reboots and kernel updates — no need to redo this step.

**Evidence / Notes**

- Root cause diagnosis: `lspci` confirmed Intel 8265 present; `modinfo iwlwifi` initially failed (module not found).
- After installation and reboot: `modinfo iwlwifi` succeeded; interface `wlP1s0` showed up in `ip addr`.
- Important: Interface is named **`wlP1s0`** (not `wlan0`) — need to update any hardcoded references in scripts/configs.
- OLED display container from jetbot-orin repo can display IP address on boot for quick network discovery without requiring a monitor.

**Open Items / Next Session**

- Update any scripts or Docker configs that reference `wlan0` to use the correct interface name `wlP1s0`.
- Continue with Task C: finish hardware assembly (motors, sensors configuration).
- Proceed with Task B: research and plan perception fusion workflow using jetbot-orin notebooks.

---

## Session 2026-04-20

**Planned**

- Organize project documentation and improve session tracking quality.
- Configure the Motors and finish the assembly of the robot
- Task B Research and Plan

**Accomplished**

- **WiFi Auto-Connect Configuration**
  - Configured DIGILAB WiFi to auto-connect on boot using `nmcli connection modify "DIGILAB" connection.autoconnect yes`.
  - WiFi interface `wlP1p1s0` now connects automatically; IP obtained via DHCP: `10.26.193.10`.
  - Established lookup method: `sudo arp-scan -l | grep 14:75:5b` to find Jetson on network.

- **Hardware Assembly & Power Discovery**
  - Reassembled robot with batteries installed in JetAnk chassis.
  - **Critical Finding:** JetAnk board cannot power the Jetson Orin Nano mainboard directly — batteries only power the JetAnk board and motors.
  - **Power Solution Required:** Need external power bank with voltage-regulating cable (USB-C or barrel connector) to supply ~5V to Jetson independently.
  - Started motor calibration process (in progress).

- **Python/Pip Dependency Troubleshooting**
  - Encountered broken package dependencies when attempting to install `python3-pip` (version conflict: `python3-setuptools` vs `python3-pkg-resources`).
  - System has held packages preventing installation; `dist-upgrade` did not resolve conflicts.
  - **Workaround discovered:** Created Python 3 venv using `python3 -m venv ~/jetbot-env` to bypass system pip issues.
  - venv includes its own pip, allowing installation of `pyserial` and other packages in isolated environment.

- **Documentation & Hardware Inventory**
  - Created `Jetson_Hardware_Specs.md` as comprehensive hardware reference document.
  - Populated with: OS versions (Ubuntu 22.04.5, JetPack 6.x L4T R36.4.4), CPU (6-core ARMv8), RAM (7.4 GiB), Storage (28 GiB microSD, 83% used).
  - Documented software stack: Docker 28.2.2, TensorRT 10.3.0.30, OpenCV 4.8.0, NumPy 1.21.5, cuDNN 9.3.0.75.
  - Network info: WiFi MAC `14:75:5b:0e:a4:9d`, I2C bus 7 (Qwiic) detected with devices at 0x30-0x3F range.
  - Created `collect_hardware_info.sh` script for automated hardware reporting.

**Evidence / Notes**

- Network lookup command stored in `Jetson_Hardware_Specs.md` for quick IP discovery.
- Power bank requirement is blocking Task C completion — need to source appropriate power supply before proceeding with full assembly.
- Python venv successfully created; can now use `pip` within venv environment without system package conflicts.
- **I2C Bus 7 Verification:** `sudo i2cdetect -y 7` confirms bus is functional and ready; no devices detected yet (expected during assembly phase).
- **Cameras:** Not yet connected; will be integrated later in Task C.
- Hardware specs document is production-ready; includes quick reference table and detailed sections.
- Verified I2C connectivity at addresses 0x30-0x3F range will populate once motor driver, OLED, and sensors are installed.

**Open Items / Next Session**

- **Critical:** Procure external power bank with voltage-regulating cable to power Jetson Orin Nano mainboard independently.
- Resume motor calibration once power solution is in place.
- Test I2C peripheral detection on bus 7 to identify attached Qwiic devices.
- Install v4l-utils and enumerate camera devices (`v4l2-ctl --list-devices`).
- Continue Task B: Research perception fusion workflow using jetbot-orin reference notebooks.
- Document final power supply specifications in `Jetson_Hardware_Specs.md` once obtained.

---

## Session 2026-04-26

**Planned**

- Resolve remaining Python/pip dependency issues
- Research and identify external power solution for Jetson Orin Nano

**Accomplished**

- **Python/pip Installation (Direct Method)**
  - System Python 3 did not have pip as a built-in module; venv workaround was insufficient for general package management.
  - Used `curl` to directly install pip from PyPA bootstrap script: `curl https://bootstrap.pypa.io/get-pip.py | python3`
  - Successfully installed pip system-wide; can now use `pip3` directly without venv activation.
  - Installed `pyserial` package via pip: `pip3 install pyserial`
  - Verified serial module works: `python3 -c "import serial; print(serial.__version__)"`

- **External Power Solution Research**
  - Researched Jetson Orin Nano power requirements and compatible power delivery options.
  - **Identified Solution:** Need USB-C PD (Power Delivery) power bank or standard USB-C charger with voltage regulator capable of:
    - Output: 5V 2A (minimum) for Jetson mainboard
    - USB-C connector with proper power profile
    - Alternative: Barrel connector (5.5mm x 2.1mm) adapter with voltage regulator if using non-USB-C power bank
  - **Cable Specifications:**
    - USB-C to Jetson barrel connector cable with integrated voltage regulator (recommended)
    - OR separate USB-C power bank + USB-C to barrel adapter + voltage regulation module
  - Documented power solution requirements for procurement

**Evidence / Notes**

- `curl | python3` method bypassed apt package manager conflicts entirely.
- Direct pip installation is more maintainable than venv-only approach for system-wide packages.
- Power bank solution options identified; ready for procurement.
- Voltage regulation is critical — cannot directly use 5V output without regulation for stable Jetson operation.

**Open Items / Next Session**

- Procure USB-C PD power bank or equivalent power delivery solution.
- Source appropriate voltage-regulating cable (USB-C barrel with regulation or separate modules).
- Once power cable obtained: test power delivery to Jetson mainboard independently.
- Resume full hardware assembly (motors, sensors) once power verified working.
- Continue Task B: Perception fusion research with confirmed power stability.

