#!/bin/bash
echo "=== System Info ==="
cat /proc/device-tree/model 2>/dev/null || echo "Model info not available"
echo ""
uname -a

echo -e "\n=== Camera Config ==="
grep -E "camera|dtoverlay" /boot/firmware/config.txt 2>/dev/null || grep -E "camera|dtoverlay" /boot/config.txt

echo -e "\n=== Kernel Messages (Camera) ==="
dmesg | grep -E "imx|cam|csi|unicam|pisp" | tail -n 30

echo -e "\n=== Libcamera Tools ==="
if command -v rpicam-hello &> /dev/null; then
    echo "rpicam-hello found, running list-cameras..."
    rpicam-hello --list-cameras
elif command -v libcamera-hello &> /dev/null; then
    echo "libcamera-hello found, running list-cameras..."
    libcamera-hello --list-cameras
else
    echo "No libcamera/rpicam tools found."
fi
