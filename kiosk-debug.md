# Kiosk troubleshooting (step-by-step)

Step-by-step guide for debugging the Pi Weather Dashboard kiosk and backend. Use this when the screen is blank, the browser won’t start, or **the dashboard isn’t updating** (stale data, “Weather data unavailable”, or the page never refreshes).

---

## Quick checklist

- [ ] **Boot mode:** Pi is set to **Desktop** (or Desktop Autologin), not Console.
- [ ] **Docker:** Backend container is running: `docker ps` shows `pi_weather_dashboard`.
- [ ] **Backend reachable:** `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/` returns `200`, `301`, or `302`.
- [ ] **Kiosk service (if used):** `systemctl --user status weather-kiosk.service` is **active (running)**.
- [ ] **Wayland:** Restart kiosk from a **terminal on the Pi desktop**, not over SSH.

---

## 1. Dashboard not updating (stale data or “Weather data unavailable”)

If the dashboard shows old data, never refreshes, or shows “Weather data unavailable”, the problem is usually the **Flask app inside Docker**: the container may be stuck, not reading updated `.env`, or failing to reach the Weather API. Recreating the container often fixes it.

### 1.1 Check backend and logs

From the Pi (in the project directory):

```bash
cd ~/pi-weather-dashboard
docker ps
```

- If `pi_weather_dashboard` is **not** in the list, the container isn’t running. Go to [1.2 Recreate the Docker container](#12-recreate-the-docker-container).
- If it **is** running, check logs for API or startup errors:

```bash
docker logs pi_weather_dashboard 2>&1 | tail -80
```

Look for:

- `No observations` / invalid API response → fix `WU_API_KEY` and `WU_STATION_ID` in `.env`, then recreate the container.
- Python tracebacks or “Address already in use” → recreate the container (and ensure no other process is using port 5000).

### 1.2 Recreate the Docker container

Recreating the container forces a clean start, reloads `.env`, and can fix stuck or misconfigured state. Do this when:

- The dashboard isn’t updating or shows “Weather data unavailable” after you fixed `.env`.
- Backend logs show repeated errors and a simple restart didn’t help.
- You changed `requirements.txt` or `Dockerfile` and want those changes applied.

**Steps (from `~/pi-weather-dashboard`):**

```bash
cd ~/pi-weather-dashboard

# 1. Stop and remove the existing container (and its associated resources)
docker compose down

# 2. (Optional but recommended) Rebuild the image so code/dependency changes are picked up
docker compose build --no-cache

# 3. Start the container again
docker compose up -d

# 4. Confirm it’s running
docker ps
```

**Verify the backend:**

```bash
# Should return 200, 301, or 302
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/

# Optional: fetch the debug inside-sensor endpoint if you use HA sensors
curl -s http://localhost:5000/api/debug/inside-sensor
```

After recreating, wait a few seconds and reload the dashboard in the kiosk (or restart the kiosk). The dashboard should start updating again; if not, re-check `docker logs pi_weather_dashboard` and `.env` (API key, station ID, HA URLs/tokens).

**Quick one-liner (full recreate with rebuild):**

```bash
cd ~/pi-weather-dashboard && docker compose down && docker compose build --no-cache && docker compose up -d
```

---

## 2. Kiosk not displaying (blank or no browser window)

### 2.1 Boot mode must be Desktop

The kiosk needs a graphical session (Wayland/labwc). If the Pi boots to **Console** instead of **Desktop**, the browser won’t have a display.

- **Raspberry Pi Configuration:** `sudo raspi-config` → **System Options** → **Boot / Auto Login** → choose **Desktop** or **Desktop Autologin**.
- Reboot after changing.

### 2.2 Autostart not running

- **Option A (systemd):** labwc should start the user service via `~/.config/labwc/autostart`. Check:
  - `ls -la ~/.config/labwc/autostart` — should be the `labwc-autostart` script (or a copy) and **executable** (`chmod +x`).
  - After login, `systemctl --user status weather-kiosk.service` should be **active (running)**.
- **Option B (script-only):** `~/.config/labwc/autostart` should be a copy of `kiosk.sh` and executable.

If the service never starts, see **kiosk-setup.md** for installing the service and labwc autostart.

### 2.3 Manual run (to see errors in the terminal)

Stop the service so it doesn’t fight with a manual run:

```bash
systemctl --user stop weather-kiosk.service
```

From a **terminal on the Pi desktop** (not SSH):

```bash
cd ~/pi-weather-dashboard
./kiosk.sh
```

The script runs in the foreground and logs to `/tmp/weather-kiosk.log`. You’ll see when it waits for Flask, which Chromium it uses, and any Chromium errors. Close the browser window to exit. When done testing, start the service again:

```bash
systemctl --user start weather-kiosk.service
```

---

## 3. Chromium: install and keyring popup

### 3.1 Chromium not found

If the kiosk log says Chromium wasn’t found:

```bash
sudo apt update
sudo apt install chromium
```

On some images the binary is `chromium-browser`; `kiosk.sh` checks both. Then run `./kiosk.sh` again or restart the service.

### 3.2 “Default Keyring” / unlock prompt

When Chromium starts for the first time (or in a new profile), it may ask to unlock the “Default Keyring”. This is normal.

- Set a password once (or leave blank if you prefer).
- Enable **Unlock on login** so the kiosk doesn’t block on every boot.
- After that, the prompt shouldn’t appear again for that profile.

The kiosk profile is under `~/.local/share/weather-kiosk-chromium` (or `$XDG_DATA_HOME/weather-kiosk-chromium`).

---

## 4. Wayland and “browser doesn’t relaunch after restart”

The kiosk needs a Wayland display. If you restart the service **over SSH**, the user session often doesn’t have `WAYLAND_DISPLAY` set, so the new Chromium process can’t open a window.

- **Always run `./restart-kiosk.sh` (or `systemctl --user restart weather-kiosk.service`) from a terminal on the Pi desktop.**

Check the kiosk log:

```bash
cat /tmp/weather-kiosk.log
```

- You should see `WAYLAND_DISPLAY=wayland-1` (or similar). If you see **WARNING: WAYLAND_DISPLAY is not set**, the restart was not done in a graphical session.
- After “Launching Chromium...”, if Chromium exits immediately with a non-zero code, the log may show a Wayland or GPU error.

More detail: **kiosk-setup.md** → “If the browser doesn’t relaunch after restart”.

---

## 5. Where to look: logs and commands

| What you want           | Command / location |
|-------------------------|---------------------|
| Backend (Flask) logs    | `docker logs -f pi_weather_dashboard` |
| Last 50 lines of backend | `docker logs pi_weather_dashboard 2>&1 \| tail -50` |
| Kiosk script + Chromium | `cat /tmp/weather-kiosk.log` |
| Is container running?   | `docker ps` |
| Restart backend only    | `docker compose restart` (same image) |
| Recreate backend        | See [1.2 Recreate the Docker container](#12-recreate-the-docker-container) |
| Kiosk service status    | `systemctl --user status weather-kiosk.service` |
| Restart kiosk           | `./restart-kiosk.sh` (from desktop terminal) |

The line in the kiosk log containing `crashpad/snapshot/elf/elf_dynamic_array_reader.h:64 tag not found` is a known, harmless Chromium/Crashpad message on Pi and can be ignored.

---

## 6. Screen blanking

If the display turns off after a while:

- **Raspberry Pi Configuration** → **Display** → set **Screen Blanking** to **Disabled**.

---

For installation and service setup, see **kiosk-setup.md**. For API/backend and Inside sensor issues, see the **Troubleshooting** section in **README.md**.
