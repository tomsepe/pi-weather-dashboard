1. The Correct Autostart Location for Trixie
In Trixie, the user-specific autostart file should be located in ~/.config/labwc/. You likely need to create this directory.

Run these commands:

```Bash
# Create the directory if it doesn't exist
mkdir -p ~/.config/labwc
```

# Move or link your kiosk script there so it's managed by labwc
# We will create a fresh one to ensure it's Wayland-compatible
```Bash
nano ~/.config/labwc/autostart
```

2. The Wayland-Optimized Autostart Script
Wayland handles screen management differently than X11 (it doesn't use xset). Replace the content of your autostart file with this.

Paste this into ~/.config/labwc/autostart:

```Bash
#!/bin/bash

# 1. Give Docker a few seconds to spin up the Flask app
sleep 8

# 2. Launch Chromium with Wayland-specific flags for the 7" screen
# Note: --ozone-platform=wayland is key for Trixie
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --ozone-platform=wayland \
  --window-size=800,480 \
  --window-position=0,0 \
  http://localhost:5000 &
```

Make it executable:

```Bash
chmod +x ~/.config/labwc/autostart
```

3. Handling Screen Blanking (The Wayland Way)
Since xset won't work on Trixie's default Wayland setup, you handle "always-on" display settings through the Labwc configuration or the OS Power settings.

The Easy Way: Go to Menu > Preferences > Raspberry Pi Configuration > Display and ensure "Screen Blanking" is Disabled. This is a persistent system setting that Trixie respects.

4. Why this is better for your Pi 4
Zero Extra Services: We aren't adding a new systemd service or a heavy manager; we are simply dropping a script into the folder the desktop is already programmed to look at.

Hardware Acceleration: Using the --ozone-platform=wayland flag ensures Chromium uses the Pi 4's GPU properly, which keeps your Tiny House dashboard snappy.
