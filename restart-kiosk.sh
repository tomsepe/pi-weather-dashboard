#!/bin/bash
# Start or restart the weather kiosk without rebooting.
# Run from the Pi: use a terminal on the desktop (Wayland env required).
# If run over SSH, the service may not have Wayland—run from a desktop terminal instead.

if systemctl --user is-active --quiet weather-kiosk.service 2>/dev/null; then
  echo "Restarting kiosk..."
  systemctl --user restart weather-kiosk.service
else
  echo "Starting kiosk..."
  systemctl --user start weather-kiosk.service
fi
echo "Waiting for startup..."
sleep 6

# Show whether the service is running and recent log output
echo ""
echo "--- Service status ---"
systemctl --user status weather-kiosk.service --no-pager -l || true
echo ""
echo "--- Last 20 lines of kiosk log (full log: /tmp/weather-kiosk.log) ---"
if [ -f /tmp/weather-kiosk.log ]; then
  tail -20 /tmp/weather-kiosk.log
else
  echo "(log file not found yet)"
fi
echo ""
echo "If the browser did not appear: check WAYLAND_DISPLAY in the log above."
echo "If it says 'not set', run this script from a terminal on the Pi desktop (not SSH)."
