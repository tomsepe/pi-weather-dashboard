#!/bin/bash

# 1. Wait for the Flask Docker container to be ready
sleep 10

# 2. Hide the mouse cursor after 0.1s of inactivity
unclutter -idle 0.1 -root &

# 3. Disable screen blanking and power management
xset s noblank
xset s off
xset -dpms

# 4. Launch Chromium in Kiosk mode
# We point to localhost:5000 where your Docker container is mapped
/usr/bin/chromium-browser --noerrdialogs --disable-infobars --kiosk --window-size=800,480 --window-position=0,0 http://localhost:5000
