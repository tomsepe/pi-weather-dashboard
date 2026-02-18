#!/bin/bash
# Restart the weather kiosk without rebooting.
# Run from the Pi: use a terminal on the desktop (Wayland env required for relaunch).
# If run over SSH, the restarted service may not have Wayland—run from a desktop terminal instead.

if ! systemctl --user is-active --quiet weather-kiosk.service 2>/dev/null; then
  echo "weather-kiosk.service not running. Start it with: systemctl --user start weather-kiosk.service"
  echo "Or run the kiosk script directly: ./kiosk.sh"
  exit 1
fi

echo "Stopping kiosk..."
systemctl --user restart weather-kiosk.service
echo "Kiosk service restarted. Waiting a few seconds for startup..."
sleep 4

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
