#!/bin/bash
# Restart the weather kiosk without rebooting.
# Run from the Pi (terminal on desktop or SSH): ./restart-kiosk.sh

if systemctl --user is-active --quiet weather-kiosk.service 2>/dev/null; then
  systemctl --user restart weather-kiosk.service
  echo "Kiosk restarted."
else
  echo "weather-kiosk.service not running. Start it with: systemctl --user start weather-kiosk.service"
  echo "Or run the kiosk script directly: ./kiosk.sh"
  exit 1
fi
