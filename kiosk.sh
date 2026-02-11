#!/bin/bash
# Kiosk launcher for Pi Weather Dashboard
# Use this on Raspberry Pi OS Trixie (Wayland/labwc). For autostart, copy this
# script's contents into ~/.config/labwc/autostart and run: chmod +x ~/.config/labwc/autostart

# 1. Wait for the Flask Docker container to be ready
sleep 10

# 2. Launch Chromium in Kiosk mode (Wayland on Trixie)
# --ozone-platform=wayland is required for labwc; without it the browser may not display.
/usr/bin/chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --ozone-platform=wayland \
  --window-size=800,480 \
  --window-position=0,0 \
  http://localhost:5000
