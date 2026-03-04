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
- **Kiosk log:** `cat /tmp/weather-kiosk.log`

If the browser doesn’t relaunch after restart, see **kiosk-debug.md** (section 4).

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

For troubleshooting (browser won’t relaunch, screen blanking, Wayland, logs), see **kiosk-debug.md**.
