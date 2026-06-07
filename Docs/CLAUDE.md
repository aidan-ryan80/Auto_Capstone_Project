# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autonomous JetBot using **Jetson Orin Nano Super** (hostname: `jetbot-04`, JetPack 6.x / L4T R36.4.4). Three capstone tasks:
- **Task C:** Hardware assembly + Jetson platform integration
- **Task B:** Camera fusion for perception (lane + object detection)
- **Task A:** Camera fusion for autonomous driving control

Reference implementation: [moatazsawi/jetbot-orin](https://github.com/moatazsawi/jetbot-orin)

---

## Hardware Access

```bash
# Find Jetson IP on DIGILAB network
sudo arp-scan -l | grep 14:75:5b

# SSH into Jetson
ssh jetbot@$(sudo arp-scan -l | grep 14:75:5b | awk '{print $1}')
```

- WiFi interface: `wlP1p1s0` (NOT `wlan0` — JetPack 6.x predictable naming)
- Ethernet fallback: `enP8p1s0`
- WiFi MAC: `14:75:5b:0e:a4:9d`
- Qwiic I2C bus: `/dev/i2c-7` (`sudo i2cdetect -y 7`)

---

## Development Workflow (on Jetson)

ML work runs inside Docker containers, not via local pip:

```bash
# Start containers (from jetbot-orin repo root)
./scripts/run-display.sh     # OLED display container
./scripts/run-ml.sh          # ML + Jupyter container

# Jupyter reachable at http://<jetson_ip>:8888
```

For Python outside Docker, use the venv (system pip is broken due to package conflicts):
```bash
source ~/jetbot-env/bin/activate
pip install <package>
```

---

## Useful Diagnostics

```bash
# Camera enumeration (once CSI camera connected)
v4l2-ctl --list-devices

# Enable CSI camera if missing
sudo python3 /opt/nvidia/jetson-io/jetson-io.py  # then reboot

# I2C peripheral check
sudo i2cdetect -y 7

# Refresh hardware docs
./scripts/collect_hardware_info.sh Docs/Jetson_Hardware.md
```

---

## Architecture

### Perception pipeline (Task B target)
Per-frame fused state output:
```json
{
  "lane_offset": 0.10,
  "lane_conf": 0.84,
  "obstacle": {"class": "person", "conf": 0.92, "distance_m": 1.7},
  "risk_level": "high",
  "action_hint": "stop"
}
```
Sources: `notebooks/road_following/` (lane) + `notebooks/object_following/` (YOLO object).

### Control policy (Task A target)
- Lane centered + clear → move forward
- Lane offset → steering correction
- High risk or low confidence → slow/stop
- Safety gates: confidence threshold, obstacle-distance threshold, manual e-stop

---

## Known Issues

| Issue | Workaround |
|-------|-----------|
| WiFi driver missing from JetPack 6.x kernel | `backport-iwlwifi-dkms` installed 2026-04-17; persists via DKMS |
| `python3-pip` broken (package conflict) | Use `~/jetbot-env` venv |
| JetAnk board cannot power Jetson mainboard | External power bank required (blocking Task C completion) |
| Storage 83% full (28 GiB total) | Monitor before pulling large Docker images |

---

## Docs

- `Docs/Capstone_Plan.md` — full task plans, milestones, fallback strategies
- `Docs/Project_Timeline.md` — session-by-session progress log
- `Docs/Jetson_Hardware_Specs.md` — hardware specs, software stack, interface details
