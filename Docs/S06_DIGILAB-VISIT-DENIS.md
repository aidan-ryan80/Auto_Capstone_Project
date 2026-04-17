# JETANK WiFi Setup — Session Notes

**Date:** 2025-04-17  
**Hardware:** Waveshare JETANK AI Kit with Jetson Orin Nano  
**OS:** JetPack 6.2 (kernel `5.15.148-tegra`)  
**Reference project:** [moatazsawi/jetbot-orin](https://github.com/moatazsawi/jetbot-orin)

---

## Background

The team flashed JetPack 6.2 for Jetson Orin Nano instead of the original JetPack image for Jetson Nano, due to hardware compatibility requirements. Most existing guides target the older Jetson Nano, so several things needed to be adapted for the Orin Nano.

The main blocker before this session was **no wireless connectivity** — the JetPack 6.x image ships with a stripped-down kernel that is missing many WiFi drivers that were present in JetPack 5.x. The board was temporarily connected via Ethernet to work around this.

---

## Root Cause

JetPack 6.x omits the `iwlwifi` kernel module, which is required for Intel WiFi cards. The board has an **Intel Wireless 8265 / 8275** card physically installed and detectable on the PCIe bus (confirmed via `lspci`), but the driver was absent from the kernel.

**Diagnosis commands used:**

```bash
uname -r
# 5.15.148-tegra

lspci | grep -i -E "network|wireless|wifi"
# 0001:01:00.0 Network controller: Intel Corporation Wireless 8265 / 8275 (rev 78)

modinfo iwlwifi
# modinfo: ERROR: Module iwlwifi not found.

ip link show
# No wireless interface present — only lo, enP8p1s0 (Ethernet), docker0, etc.
```

---

## Fix Applied

### 1. Install the backported Intel WiFi driver

With Ethernet still connected, install the DKMS backport package which compiles and installs the `iwlwifi` module against the running kernel:

```bash
sudo apt update
sudo apt install -y backport-iwlwifi-dkms
```

This takes a few minutes as DKMS compiles the module. Output showing the build process is normal.

### 2. Reboot

```bash
sudo reboot
```

After reboot, a new wireless interface appeared: **`wlP1p1s0`**  
*(Note: JetPack 6.x uses predictable interface naming — the interface will not be called `wlan0`.)*

### 3. Connect to WiFi

```bash
sudo nmcli dev wifi connect "SSID" password "password"
# Device 'wlP1p1s0' successfully activated with '[hash]'
```

Plain `nmcli` (without `sudo`) returned a "Not authorized to control networking" error — using `sudo` resolved this.

### 4. Verify connectivity

```bash
ip a
# wlP1p1s0 shows an inet address — confirms IP assigned

ping -c 4 8.8.8.8
# Successful — wireless connectivity confirmed
```

Ethernet cable was then unplugged and connectivity was verified again. **The Jetson Orin Nano is now running fully wireless.**

---

## Result

The JETANK is now connected to the LAN wirelessly and can be controlled without a tethered Ethernet cable, which is a prerequisite for the autonomous driving use case.

The `backport-iwlwifi-dkms` module is installed via DKMS and will **persist across reboots and kernel updates** — no need to redo this step.

---

## Notes for the Team

- The wireless interface is named **`wlP1p1s0`**, not `wlan0`. Update any scripts or configs that hardcode `wlan0`.
- The OLED display container from the jetbot-orin repo will show the IP address on boot — use this to find the board's IP on the network without needing a monitor.
- Next step is to follow the [jetbot-orin setup guide](https://github.com/moatazsawi/jetbot-orin) to pull the Docker images and get JupyterLab running for the notebook-based driving tasks.
