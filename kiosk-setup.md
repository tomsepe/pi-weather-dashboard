# Kiosk setup (Trixie / Wayland / labwc)

## Option A: Systemd user service (recommended)

You can **restart the kiosk without rebooting** with `systemctl --user restart weather-kiosk` or `./restart-kiosk.sh`.

### 1. Install the service

On the Pi, from the project directory:

```bash
cd ~/pi-weather-dashboard
mkdir -p ~/.config/systemd/user
cp weather-kiosk.service ~/.config/systemd/user/
```

Reload systemd so it sees the new service:

```bash
systemctl --user daemon-reload
```

### 2. Use labwc autostart to start the service when the desktop loads

```bash
mkdir -p ~/.config/labwc
cp labwc-autostart ~/.config/labwc/autostart
chmod +x ~/.config/labwc/autostart
```

### 3. Restart without rebooting

**Use a terminal on the Pi desktop** (not SSH). The restarted service needs the graphical session’s Wayland environment to open the browser again.

```bash
cd ~/pi-weather-dashboard
./restart-kiosk.sh
```

The script prints service status and the last 20 lines of the kiosk log so you can see why the window did or didn’t appear.

Or restart directly:

```bash
systemctl --user restart weather-kiosk.service
```

Useful commands:

- **Status:** `systemctl --user status weather-kiosk.service`
- **Stop:** `systemctl --user stop weather-kiosk.service`
- **Start:** `systemctl --user start weather-kiosk.service`
- **Kiosk log (script + Chromium):** `cat /tmp/weather-kiosk.log`

### If the browser doesn’t relaunch after restart

1. **Run `./restart-kiosk.sh` from a terminal on the desktop** (not SSH). Over SSH, the user systemd session often doesn’t have `WAYLAND_DISPLAY` set, so the restarted kiosk can’t open a window.
2. **Check the kiosk log:** `cat /tmp/weather-kiosk.log`  
   - Look for `WAYLAND_DISPLAY=wayland-1` (or similar). If you see `WARNING: WAYLAND_DISPLAY is not set`, the service was started without a Wayland display—run the restart from a desktop terminal.
   - Look for `Launching Chromium...` and the line after it. If Chromium exits with a non‑zero code immediately, the log may show why (e.g. Wayland connection failed).
3. **Check service status:** `systemctl --user status weather-kiosk.service`  
   - If the service is “active (running)”, the script is running but Chromium may be failing to connect to Wayland. Check the log as above.
   - If the service is “failed”, read the status output and the end of `/tmp/weather-kiosk.log` for the error.

---

## Option B: Script-only autostart (no systemd)

If you prefer not to use a service, copy the kiosk script into labwc autostart:

```bash
mkdir -p ~/.config/labwc
cp ~/pi-weather-dashboard/kiosk.sh ~/.config/labwc/autostart
chmod +x ~/.config/labwc/autostart
```

To restart you would need to log out and back in, or reboot. There is no single “restart kiosk” command.

---

## Screen blanking

Go to **Menu → Preferences → Raspberry Pi Configuration → Display** and set **Screen Blanking** to **Disabled** so the dashboard stays on.

---

## Why Wayland flags matter

Using **`--ozone-platform=wayland`** in Chromium ensures it uses the Pi’s GPU correctly under labwc. The `weather-kiosk.service` and `kiosk.sh` already use the right flags.
