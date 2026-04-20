 # JetBot Orin Nano Capstone Plan (Tasks C, B, A)

 ## Goal
 Complete all 3 capstone tasks on **Jetson Orin Nano** using the following repo as a resource:
 - https://github.com/moatazsawi/jetbot-orin

 Tasks:
 - **Task C:** Assemble vehicle + integrate Jetson platform
 - **Task B:** Camera fusion for perception (lane + object)
 - **Task A:** Camera fusion for driving (control from fused perception)

---

 ## Core References
 - JetBot Orin repo: https://github.com/moatazsawi/jetbot-orin
 - Assembly guide: `docs/README.md` in that repo
 - Runtime scripts: `scripts/run-display.sh`, `scripts/run-ml.sh`
 - Notebooks:
   - `notebooks/road_following/*`
   - `notebooks/object_following/*`
   - `notebooks/collision_avoidance/*`

---

 ## Phase 0 - Orin Baseline Environment

 1. Verify platform:
    - `uname -a`
    - `lsb_release -a`
    - `cat /proc/device-tree/model`
 2. Clone and prepare repo:
    - `git clone https://github.com/moatazsawi/jetbot-orin.git`
    - `cd jetbot-orin`
    - `chmod +x scripts/run-ml.sh scripts/run-display.sh`
 3. Pull Docker images:
    - `sudo docker pull moatazsawi/jetbot-orin-ml:36.4.0`
    - `sudo docker pull moatazsawi/jetbot-orin-display:36.4.0`
 4. Start display container:
    - `./scripts/run-display.sh`
 5. Start ML/Jupyter container:
    - `./scripts/run-ml.sh`

 **Exit criteria**
 - Jupyter reachable at `http://<jetson_ip>:8888`
 - Camera available in notebook/container
 - OLED/motor interfaces available

---

 ## Task C Plan - Build + Integration

 ### C1) Hardware assembly
 Follow `docs/README.md` (Orin-specific):
 - Chassis + motors + caster
 - Camera mount + CSI cable
 - Qwiic pHAT + OLED + motor driver chain
 - NVMe install (if used)

 ### C2) Hardware validation
 - Camera:
   - `v4l2-ctl --list-devices`
 - If CSI missing:
   - `sudo python3 /opt/nvidia/jetson-io/jetson-io.py` then reboot
 - Verify display and motor control notebooks run

 ### C3) Remote access/network
 - Keep Ethernet for initial bring-up
 - Use USB tethering fallback
 - Add USB Wi-Fi adapter later if fully wireless is required

 **Task C deliverables**
 - Fully assembled robot
 - Camera + motor + OLED validated
 - Remote notebook control working
 - Short integration demo video

---

 ## Task B Plan - Camera Fusion for Perception

 ## Objective
 Produce one fused perception state from lane + object signals.

 ### B1) Baseline modules
 - Lane baseline from `road_following` notebooks
 - Object baseline from `object_following` notebooks (YOLO)

 ### B2) Fusion output (per frame)
 Create a structured state, e.g.:
```json
 {
   "lane_offset": 0.10,
   "lane_conf": 0.84,
   "obstacle": {"class": "person", "conf": 0.92, "distance_m": 1.7},
   "risk_level": "high",
   "action_hint": "stop"
 }
```

B3) Robustness experiments

Evaluate under:

 - Lighting change
 - Shadows/glare
 - Blur
 - Partial occlusion
 - Different camera angles/resolutions

Task B deliverables

 - Live fused overlay/state
 - Logged frame-by-frame fused outputs
 - Table with FPS, confidence stability, failure cases

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Task A Plan - Camera Fusion for Driving

Objective

Convert fused perception into safe driving commands.

A1) Controller policy

 - Lane centered + clear: move forward
 - Lane offset: steering correction
 - High risk or low confidence: slow/stop

A2) Safety gates

 - Confidence threshold stop
 - Obstacle-distance threshold stop
 - Manual emergency stop path

A3) Closed-loop evaluation scenarios

 1. Normal lane following
 2. Obstacle appears in path
 3. Ambiguous perception / low-confidence case

Track:

 - Intervention count
 - Command stability/jitter
 - Safe-stop trigger reliability

Task A deliverables

 - Autonomous driving demo
 - Documented controller logic
 - Quantitative + qualitative performance summary

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Milestones

 1. M1 (Task C): Platform integrated, remote workflow running
 2. M2 (Task B): Real-time fused perception pipeline
 3. M3 (Task A): Safety-aware driving fusion and scenario demos
 4. Final package: code, demo videos, metrics tables, report narrative

------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Risks + Fallbacks

 - No usable onboard Wi-Fi driver: use Ethernet/USB tethering, then USB Wi-Fi adapter
 - Camera not detected: Jetson-IO + cable reseat + container device mapping
 - Low FPS: reduce resolution, lighter model, TensorRT variants
 - Unstable control: temporal smoothing + confidence-gated stop