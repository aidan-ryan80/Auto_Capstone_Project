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
- Moved/standardized planning context in project docs.
- Defined project path responsibilities:
  - `Auto_Capstone_Project` = main version-controlled work.
  - `jetbot-orin` = reference/example repo.
- Created first iteration of `Project_Timeline.md` focused on outcomes per session instead of only intentions.

**Evidence / Notes**
- Timeline format now enforces four sections: Planned, Accomplished, Evidence/Notes, Open Items.
- 

**Open Items / Next Session**

- 

