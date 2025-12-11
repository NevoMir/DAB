#!/bin/bash
echo "=== Raspberry Pi Model ==="
cat /proc/device-tree/model
echo -e "\n\n=== OS Release ==="
cat /etc/os-release
echo -e "\n\n=== Kernel Version ==="
uname -a
echo -e "\n\n=== Boot Config (Camera) ==="
grep -i "camera" /boot/firmware/config.txt 2>/dev/null || grep -i "camera" /boot/config.txt
echo -e "\n\n=== vcgencmd get_camera ==="
vcgencmd get_camera
echo -e "\n\n=== libcamera/rpicam List ==="
rpicam-hello --list-cameras 2>/dev/null || libcamera-hello --list-cameras
echo -e "\n\n=== dmesg (Camera/Sensor errors) ==="
dmesg | grep -E -i "cam|imx|ov5647|ov9281|fpc|csi" | tail -n 20
