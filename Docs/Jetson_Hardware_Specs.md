# Jetson Orin Nano Hardware Specifications

**Last Updated:** Mo 20 Apr 2026 14:44:59 CEST

---

## Quick Reference

| Property | Value |
|----------|-------|
| **Device Model** | Jetson Orin Nano Super |
| **Hostname** | jetbot-04 |
| **WiFi MAC Address** | `14:75:5b:0e:a4:9d` |
| **WiFi Interface** | `wlP1p1s0` |
| **Network** | DIGILAB |
| **Lookup Command** | `sudo arp-scan -l | grep 14:75:5b` |

---

## Operating System

### Ubuntu / JetPack Versions

**Ubuntu Version:**
```
Distributor ID:	Ubuntu
Description:	Ubuntu 22.04.5 LTS
Release:	22.04
Codename:	jammy
```

**JetPack Version:**
```
JetPack 6.x (L4T R36.4.4, REVISION: 4.4)
GCID: 41062509, BOARD: generic, EABI: aarch64
DATE: Mon Jun 16 16:07:13 UTC 2025
KERNEL_VARIANT: oot
```

**Kernel:**
```
Linux jetbot-orin-nano 5.15.148-tegra #1 SMP PREEMPT Thu Sep 18 15:08:33 PDT 2025 aarch64 aarch64 aarch64 GNU/Linux
```

**L4T Release:**
```
R36 (release), REVISION: 4.4, GCID: 41062509
BOARD: generic, EABI: aarch64
DATE: Mon Jun 16 16:07:13 UTC 2025
KERNEL_VARIANT: oot (out-of-tree)
```

---

## CPU & Memory

**CPU Model:**
```
ARMv8 Processor rev 1 (v8l)
```

**CPU Cores:**
```
6 cores
```

**Total RAM:**
```
7.4 GiB
```

**Available RAM:**
```
6.5 GiB (with 901 MiB cache)
Swap: 3.7 GiB (unused)
```

---

## Storage

**Primary Storage:**
```
microSD / eMMC: mmcblk0 (28GB total)
Filesystem: ext4 (mmcblk0p1)
```

**Total Size:**
```
28 GiB
```

**Free Space:**
```
4.7 GiB available (83% used)
Mounted at: /
```

---

## GPU & NVIDIA

**GPU Model:**
```
Integrated NVIDIA Orin Nano GPU (not separately identifiable via nvidia-smi)
```

**GPU Memory:**
```
Shared with system RAM (no dedicated VRAM)
```

**CUDA Version:**
```
CUDA 12.6 (not installed as standalone; integrated in JetPack/L4T)
```

**cuDNN Version:**
```
cuDNN 9.3.0.75 for CUDA 12.6
- libcudnn9-cuda-12 (runtime)
- libcudnn9-dev-cuda-12 (development)
- libcudnn9-static-cuda-12 (static libraries)
- libcudnn9-samples
```

**TensorRT Version:**
```
TensorRT 10.3.0.30 (for CUDA 12.5)
- libnvinfer10 (runtime)
- libnvinfer-dev (development)
- libnvinfer-plugin10 (plugin runtime)
- libnvinfer-lean10 (lean runtime)
- python3-libnvinfer (Python 3 bindings)
```

---

## Network & Wireless

**Ethernet Interface:**
```
enP8p1s0 (MAC: 3c:6d:66:76:ac:9b)
```

**WiFi Interface:**
```
wlP1p1s0 (MAC: 14:75:5b:0e:a4:9d)
```

**WiFi Driver:**
```
backport-iwlwifi-dkms (installed 2026-04-17)
```

**WiFi Chip:**
```
Intel Wireless 8265 / 8275 (PCIe)
```

---

## Cameras

**Available Cameras:**
```
No cameras currently connected.
Cameras will be integrated later in the assembly process.
v4l2-ctl available for enumeration once cameras are added.
```

**CSI Camera Status:**
```
Not yet installed/connected
Camera integration planned for later assembly phase (Task C continuation)
```

---

## Software Stack

**Docker Version:**
```
Docker 28.2.2, build e6534b4
```

**Docker Images in Use:**
- moatazsawi/jetbot-orin-ml:36.4.0
- moatazsawi/jetbot-orin-display:36.4.0

**Python Version:**
```
Python 3.10.12
```

**Key Python Packages:**
```
- TensorRT: 10.3.0.30 (for CUDA 12.5)
  - python3-libnvinfer
  - python3-libnvinfer-dev
  - python3-libnvinfer-dispatch
  - python3-libnvinfer-lean

- OpenCV: 4.8.0 (built-in to JetPack)
  - libopencv
  - libopencv-dev
  - libopencv-python

- NumPy: 1.21.5

Note: PyTorch, TensorFlow, and JupyterLab not found in system packages
(likely available via Docker containers from jetbot-orin repo)
```

---

## Interfaces & Peripherals

**USB Devices:**
```
Bus 002 Device 002: ID 0bda:0489 Realtek Semiconductor Corp. 4-Port USB 3.0 Hub
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 003: ID 8087:0a2b Intel Corp. Bluetooth wireless interface
Bus 001 Device 002: ID 0bda:5489 Realtek Semiconductor Corp. 4-Port USB 2.0 Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

**I2C Devices (for Qwiic/sensors):**
```
Available I2C buses: /dev/i2c-0, /dev/i2c-1, /dev/i2c-2, /dev/i2c-4, /dev/i2c-5, /dev/i2c-7, /dev/i2c-9

I2C Bus 7 (SparkFun Qwiic):
  Bus is functional and ready for peripherals
  Current probe (sudo i2cdetect -y 7):
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
  00:
  10:
  20:
  30: -- -- -- -- -- -- -- --
  40:
  50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
  60:
  70:
  
  No devices currently detected (expected - peripherals not yet connected)
  Motor driver, OLED, sensors will appear here once installed
```

**PCIe Devices:**
```
0001:01:00.0 Network controller: Intel Corporation Wireless 8265 / 8275 [8086:24fd] (rev 78)
0008:01:00.0 Ethernet controller: Realtek Semiconductor Co., Ltd. RTL8111/8168/8411 PCI Express Gigabit Ethernet Controller [10ec:8168] (rev 15)
```

---

## Assembly & Hardware Notes

### JetBot Hardware Checklist
- [ ] Jetson Orin Nano 8GB
- [ ] Motor Driver (PCA9685)
- [ ] DC Motors (x2)
- [ ] Wheels & Chassis
- [ ] CSI Camera
- [ ] Battery/Power Supply
- [ ] OLED Display
- [ ] Qwiic Connector (I2C chain)

### Known Issues & Workarounds
1. **WiFi Driver:** Intel 8265 requires `backport-iwlwifi-dkms`. Installed 2026-04-17.
2. **Interface Naming:** WiFi interface is `wlP1p1s0`, not `wlan0` — update scripts accordingly.
3. **Ethernet:** Falls back to `enP8p1s0` if WiFi is unavailable.

---

## How to Populate This Document

**On the Jetson Orin Nano:**

```bash
# SSH into the device
ssh jetbot@ip_address

# Run the hardware collection script
cd /path/to/Auto_Capstone_Project
chmod +x scripts/collect_hardware_info.sh
./scripts/collect_hardware_info.sh Docs/Jetson_Hardware.md
```

Then manually merge the output into this file, replacing `[Run collect_hardware_info.sh to populate]` placeholders.

---

## Team Reference

**For quick network lookup:**
```bash
# Find Jetson IP on DIGILAB
sudo arp-scan -l | grep 14:75:5b

# SSH into Jetson
ssh jetbot@ip_adddress

# In a single command using the arp-scan package
ssh jetbot@$(sudo arp-scan -l | grep 14:75:5b | awk '{print $1}')
```

---

**Document created:** 2026-04-20 
