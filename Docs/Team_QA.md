# Project 3 — Team Q&A

Clarifications on technical terms and project-specific notes.

---

## Q1: What is the Jetson platform?

NVIDIA Jetson is a family of embedded Linux boards with an integrated GPU designed for running neural networks on edge devices (i.e., locally, not in the cloud).

The original **Jetson Nano** was a small, low-power board released in 2019. Our board is the newer **Jetson Orin Nano Super** — same general form factor idea, but significantly more powerful (Ampere GPU architecture, 8GB RAM, much faster AI inference).

It runs **Ubuntu 22.04** via **JetPack**, which is NVIDIA's bundled OS that includes the GPU drivers, CUDA, TensorRT, and other ML tooling pre-installed.

Why we use it: it can run TensorRT-optimized neural networks fast enough for real-time robotics (target: ≥30 FPS inference).

---

## Q2: What is JetAnk, and why is there a power problem?

**JetAnk** is a robot chassis kit made by Waveshare. It provides:
- A wheeled/tank-style chassis with motors
- A carrier board that the Jetson module plugs into
- Motor drivers accessible via I2C

**The problem:** JetAnk was designed for the original **Jetson Nano**, not the Jetson Orin Nano Super. The Orin Nano Super has different power requirements — the JetAnk carrier board's power circuitry cannot supply enough current to run the Jetson mainboard. This means motors and camera are currently blocked: the robot needs an external USB-C PD power bank capable of supplying sufficient wattage directly to the Jetson.

This is our current critical blocker for completing Task C.

---

## Q3: What is camera fusion for perception?

"Perception" = the robot figuring out what is around it.

We have one camera. Two detection algorithms run on each frame simultaneously:
- **Lane detection** — finds road markings, computes how far the robot is from the center of the lane
- **Object detection (YOLO)** — detects obstacles (people, objects) and estimates distance

"Fusion" means we merge both outputs into a single **scene state** per frame:

```json
{
  "lane_offset": 0.10,
  "lane_conf": 0.84,
  "obstacle": {"class": "person", "conf": 0.92, "distance_m": 1.7},
  "risk_level": "high",
  "action_hint": "stop"
}
```

Instead of the robot only knowing about lanes OR only about obstacles, it knows about both at once — a more complete picture of the environment.

---

## Q4: What is camera fusion for autonomous driving control?

This is the step after perception. The fused scene state from Q3 is fed into a **control policy** that decides what the motors should do:

| Situation | Action |
|-----------|--------|
| Lane centered, no obstacle | Move forward |
| Lane offset (drifting left/right) | Steer to correct |
| Obstacle detected nearby | Slow down or stop |
| Low detection confidence | Stop and wait |

"Camera fusion" here means both lane data and obstacle data influence the motor commands at the same time, rather than one source overriding the other blindly.

---

## Q5: What is the Qwiic I2C bus?

**I2C** (Inter-Integrated Circuit) is a simple two-wire serial communication protocol used to talk to peripherals like motor controllers, sensors, and displays. Many components on the JetAnk chassis communicate this way.

**Qwiic** is SparkFun's standardized connector system built on top of I2C — a small 4-pin JST connector (no soldering required) that daisy-chains devices on the same bus.

On our Jetson, the Qwiic/I2C bus is accessible at `/dev/i2c-7`. You can scan what's connected with:

```bash
sudo i2cdetect -y 7
```

---

## Q6: What is a CSI camera?

**CSI** = Camera Serial Interface (MIPI standard). It connects a camera directly to the processor via a flat ribbon cable rather than USB.

Advantages over USB cameras:
- Much lower latency
- Lower CPU overhead (data goes directly to the image signal processor)
- Required for real-time computer vision at high frame rates

The Jetson Orin Nano has a dedicated CSI port. It requires one-time kernel configuration via `jetson-io.py` before it shows up as `/dev/video0`. We have not connected the CSI camera yet — this is blocked by the power issue (see Q2).

---

## Q7: What is a manual e-stop?

**E-stop** = emergency stop. A mechanism that immediately cuts all motor power regardless of what the autonomy software is commanding.

"Manual" means a human triggers it — either by pressing a physical button wired to the motor controller, or by a keyboard shortcut in the control software.

Why it matters: if the robot starts behaving unexpectedly (steering into a wall, not stopping for obstacles), a human can halt it instantly without having to kill the software process or unplug the battery. It is a standard safety requirement for any mobile robot.

In our implementation plan, the e-stop is a software gate in the control loop that the operator can trigger at any time.

---

## Q8: What exact command did Denis run to bootstrap pip?

JetPack ships a stripped-down Python 3 that does not include `pip` or `venv`. Installing via apt (`sudo apt install python3-pip`) fails due to a version conflict between `python3-setuptools` and `python3-pkg-resources`.

Denis bypassed this entirely by downloading pip directly from the Python Packaging Authority:

```bash
curl https://bootstrap.pypa.io/get-pip.py | python3
```

This installs pip system-wide without touching apt. After that, packages install normally:

```bash
pip3 install pyserial
```

This method works because it bypasses the apt package manager conflicts entirely. The `curl | python3` approach is the official PyPA fallback for environments where the package manager's pip is broken or missing.
