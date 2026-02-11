# Kiosk not showing on Pi touchscreen – debug steps

Run these **on the Raspberry Pi** (SSH is fine for the first steps; the manual test needs the desktop).

## 1. Confirm autostart is in place

```bash
ls -la ~/.config/labwc/autostart
cat ~/.config/labwc/autostart
```

- If the file is missing, create the dir and file:
  ```bash
  mkdir -p ~/.config/labwc
  nano ~/.config/labwc/autostart
  ```
  Paste the contents of `kiosk.sh` from this repo, save, then:
  ```bash
  chmod +x ~/.config/labwc/autostart
  ```

## 2. Check the kiosk log (after a reboot)

The script logs to `/tmp/weather-kiosk.log`. After booting with the desktop:

```bash
cat /tmp/weather-kiosk.log
```

- If the file is missing, labwc probably didn’t run the script (e.g. you’re not booting to the graphical desktop, or autostart path is wrong).
- If you see “Flask ready” and “Using: /usr/bin/…” then the script ran; any error after that is from Chromium.

## 3. Boot to desktop, not console

- **Raspberry Pi Configuration** → **System** → **Boot** → set to **Desktop Autologin** (or “Desktop” with auto-login).
- Reboot. The kiosk only runs when the **labwc desktop session** starts.

## 4. Run the kiosk by hand (on the Pi, with screen and keyboard)

Log in to the **desktop** on the Pi (not SSH). Open a **terminal** and run:

```bash
cd ~/pi-weather-dashboard
./kiosk.sh
```

Watch the terminal for errors. If Chromium fails (e.g. “cannot open display”, “ozone-platform”, or missing library), that message will point to the fix.

## 5. Test the dashboard in a normal browser (on the Pi)

On the Pi desktop, open Chromium normally and go to:

`http://127.0.0.1:5000`

- If the page loads here but the kiosk still doesn’t show, the problem is how the kiosk is started (autostart or Chromium flags).
- If it doesn’t load, the problem is Docker/network (e.g. `docker ps` and `curl http://127.0.0.1:5000` from the Pi).

## 6. Confirm Chromium is installed

```bash
which chromium chromium-browser
dpkg -l | grep -i chromium
```

If not installed:

```bash
sudo apt update
sudo apt install chromium
```

---

**Quick checklist**

- [ ] Boot set to **Desktop** (autologin).
- [ ] `~/.config/labwc/autostart` exists, has the script, and is **executable** (`chmod +x`).
- [ ] `docker ps` shows `pi_weather_dashboard` and port 5000.
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/` returns 200 (or 301/302).
- [ ] After reboot, check `/tmp/weather-kiosk.log` for errors.
