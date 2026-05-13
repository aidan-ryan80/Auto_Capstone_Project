# Guide on how to set up the camera

We will access it with one of the following:
- NVIDIA Argus
- GStreamer
- OpenCV with a GStreamer pipeline


Steps:
1. Confirm hardware connection 
2. Confirm the Jetson detects the camera 
3. Test live camera preview 
4. Test camera from Python/OpenCV 
5. Integrate into your capstone AI pipeline later

Do NOT start with YOLO or ROS yet.

## Step 1 - Checking the Physical Camera Connection
https://www.youtube.com/watch?v=qNy1hulFk6I&t=534s
13:05

On the Orin Nano:
- Camera goes into the CSI camera port 
- Blue side of ribbon usually faces outward (depends on board orientation)
- Connector latch must be fully locked

Important:
The Jetson Orin Nano CAM0 and CAM1 ports are not always 
interchangeable with all camera modules.

If one port fails: try the other CSI port.

## Step 2 — Verify the Camera is Detected

Open terminal on the Jetson and run:
```dash
ls /dev/video*
```

You may or may not see:
```dash
/dev/video0
```

For CSI cameras, more important is:
```dash
dmesg | grep imx
```

or:
```dash
v4l2-ctl --list-devices
```

If working, you should see something mentioning:
- imx219
- vi-output 
- nvargus

## Step 3 — The Most Important Test

Run NVIDIA’s built-in camera test:
```bash
gst-launch-1.0 nvarguscamerasrc ! nvvidconv ! xvimagesink
```

If everything works:
 a live camera window opens.

This is the single best diagnostic test for Jetson CSI cameras.


## Step 4 — Testing the Camera in Python
This is probably what your capstone will actually need.

Install OpenCV first:
```bash
sudo apt update
sudo apt install python3-opencv
```

Then create:
```python
import cv2

pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! "
    "nvvidconv flip-method=0 ! "
    "video/x-raw, format=BGRx ! "
    "videoconvert ! "
    "video/x-raw, format=BGR ! appsink"
)

cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

Save as:
```bash
camera_test.py
```

Run:
```bash
python3 camera_test.py
```


## Possible ways to trouble shoot:

### First Thing to Check

Run:
```bash
ls /dev/video*
```

AND:
```bash
v4l2-ctl --list-devices
```

If v4l2-ctl is missing:
```bash
sudo apt install v4l-utils
```

### What You WANT to See

Something like:
```bash
NVIDIA Tegra Video Input Device
```
or:
```bash
vi-output, imx219 ...
```

This confirms:
- kernel sees camera 
- CSI lane communication works 
- device tree is correct

### MOST IMPORTANT TEST (JetPack 6)

Run:
```bash
gst-launch-1.0 nvarguscamerasrc ! \
'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
nvvidconv ! \
xvimagesink
```


If desktop/X11 is not working, use:
```bash
gst-launch-1.0 nvarguscamerasrc num-buffers=100 ! \
'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
nvvidconv ! \
videoconvert ! \
x264enc ! \
mp4mux ! \
filesink location=test.mp4 -e
```

Then:
```bash
ls
```

You should get:
```bash
test.mp4
```

That proves the camera pipeline works even without GUI.

## VERY IMPORTANT: JetPack 6 Camera Service

JetPack 6 uses:
```bash
nvargus-daemon
```

Check it:
```bash
systemctl status nvargus-daemon
```

If broken:
```bash
sudo systemctl restart nvargus-daemon
```
This daemon failing is EXTREMELY common.

#
### If Camera Is NOT Detected

Run:
```bash
dmesg | grep -i imx
```

AND:
```bash
dmesg | grep -i cam
```

#### Healthy output usually contains the following:
```bash
imx219
tegra-camrtc
registered sensor
subdev
```


#### Bad signs:
```bash
I2C timeout
no acknowledge
probe failed
```


#### Those usually mean:

- ribbon cable reversed
- connector not seated 
- damaged cable 
- wrong CSI port


## IMPORTANT ABOUT THE ORIN NANO CSI PORTS

#### On the Orin Nano developer board:

- CAM0 and CAM1 are NOT always equally configured
- many tutorials assume CAM0

#### If detection fails:

- power off completely
- move camera to other CSI connector
- retry

Do NOT hotplug CSI cameras.


### Install Useful Packages

Run:
```bash
sudo apt update

sudo apt install -y \
v4l-utils \
gstreamer1.0-tools \
gstreamer1.0-plugins-good \
gstreamer1.0-plugins-bad \
gstreamer1.0-libav \
python3-opencv
```


### (apparently) BEST OpenCV Test for JetPack 6

Use this exact code:
```python
import cv2

gst_pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! "
    "nvvidconv ! "
    "video/x-raw, format=BGRx ! "
    "videoconvert ! "
    "video/x-raw, format=BGR ! appsink"
)

cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Camera failed to open")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read frame")
        break

    cv2.imshow("Jetson Camera", frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

```

Save as:
```bash
nano test_camera.py
```

Run:
```bash
python3 test_camera.py
COMMON JETPACK 6 ISSUE
```

#### Sometimes OpenCV is built WITHOUT GStreamer support.

Check:
```bash
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep GStreamer
```

#### You want:
```bash
GStreamer: YES
```

#### If it says NO:

- install NVIDIA’s OpenCV package
- or use pure GStreamer first

But Ubuntu packages on JetPack 6 usually work.



## (Apparently) BEST DEBUGGING ORDER

### Do these EXACTLY in order:

1. systemctl status nvargus-daemon 
2. ls /dev/video*
3. v4l2-ctl --list-devices 
4. gst-launch-1.0 nvarguscamerasrc ! nvvidconv ! xvimagesink 
5. python3 test_camera.py

### One More Important Thing

If you SSH into the Jetson remotely:
```bash
cv2.imshow()
xvimagesink
```
may fail because no display exists.

In that case:
- record video to file 
-  or stream over network

or use:
```bash
export DISPLAY=:0
```
depending on the setup.


### One of these three things will happen:

#### Best case

Everything works immediately.

#### Medium case

nvargus-daemon crashed.

#### Most likely hardware issue
Ribbon cable orientation/seat issue