#!/bin/bash
# Kiosk launcher for Pi Weather Dashboard (Trixie / Wayland / labwc)
# Copy to ~/.config/labwc/autostart and: chmod +x ~/.config/labwc/autostart

LOG=/tmp/weather-kiosk.log
exec > "$LOG" 2>&1
echo "=== $(date) kiosk starting ==="

# 1. Wait for Flask to be reachable (Docker may need a few seconds after boot)
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 1 http://127.0.0.1:5000/ 2>/dev/null | grep -q '200\|301\|302'; then
    echo "Flask ready after ${i}s"
    break
  fi
  sleep 1
done

# 2. Find Chromium (name differs: chromium vs chromium-browser)
CHROMIUM=""
for c in /usr/bin/chromium /usr/bin/chromium-browser; do
  if [ -x "$c" ]; then
    CHROMIUM="$c"
    break
  fi
done
if [ -z "$CHROMIUM" ]; then
  echo "ERROR: Chromium not found. Install with: sudo apt install chromium"
  exit 1
fi
echo "Using: $CHROMIUM"

# 3. Launch in kiosk mode (Wayland). Runs in foreground so script waits until
#    Chromium exits—if you run this manually, the terminal won't return until you close the window.
#    When the "Default Keyring" prompt appears, set a password once and enable "Unlock on login".
#    GCM/registration_request errors in the log are harmless (Chromium phoning Google); ignore them.
export WAYLAND_DEBUG=0
"$CHROMIUM" \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-background-networking \
  --disable-sync \
  --ozone-platform=wayland \
  --window-size=800,480 \
  --window-position=0,0 \
  http://127.0.0.1:5000

echo "=== $(date) chromium exited (code $?) ==="
