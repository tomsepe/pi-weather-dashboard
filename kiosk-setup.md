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

If your user UID is **not** 1000 (check with `id -u`), edit the service file and change `1000` in `XDG_RUNTIME_DIR=/run/user/1000` to your UID:

```bash
nano ~/.config/systemd/user/weather-kiosk.service
# Change 1000 to your UID in the Environment=XDG_RUNTIME_DIR= line
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

From the Pi (terminal on the desktop or SSH as the same user):

```bash
cd ~/pi-weather-dashboard
./restart-kiosk.sh
```

Or directly:

```bash
systemctl --user restart weather-kiosk.service
```

Useful commands:

- **Status:** `systemctl --user status weather-kiosk.service`
- **Stop:** `systemctl --user stop weather-kiosk.service`
- **Start:** `systemctl --user start weather-kiosk.service`
- **Log (script output):** `cat /tmp/weather-kiosk.log`

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
