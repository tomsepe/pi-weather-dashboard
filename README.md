### Pi Weather Dashboard

**README.md**

# Tiny House Weather Dashboard  
A standalone, kiosk-mode weather dashboard for the Raspberry Pi 4 & 7" Touchscreen. Choose your location (city name, latitude/longitude) in the in-app **Settings** page. Optionally use a **Vevor 7-in-1** (or other) personal weather station for live “Outside” conditions via the Weather Underground API; otherwise the app uses location-based current conditions and forecast from the same API.

## 🛠 Tech Stack  
* ****Hardware:**** Raspberry Pi 4, 7" DSI Touchscreen; optional Vevor or other PWS.  
* ****OS:**** Raspberry Pi OS (Debian 13 "Trixie") using ****Wayland/labwc****.  
* ****Backend:**** Python 3.11 (Flask) running in ****Docker****.  
* ****Frontend:**** HTML5 / CSS Grid (Optimized for 800x480 resolution).

## 📁 Project Structure  
```text  
pi-weather-dashboard/  
├── app.py                  \# Flask application logic  
├── config/                 \# Created at runtime; config/settings.json (location, Vevor, screensaver)  
├── docker-compose.yaml     \# Docker service configuration  
├── Dockerfile              \# Container build instructions  
├── requirements.txt        \# Python dependencies  
├── templates/  
│   ├── dashboard.html      \# Home: Inside + optional Outside + forecast  
│   ├── dashboard_5day.html \# 5-day forecast  
│   ├── dashboard_ha.html   \# Home Assistant controls  
│   ├── dashboard_ha_settings.html \# HA entity picker  
│   ├── settings.html       \# App settings (location, Vevor, screensaver)  
│   └── _screensaver.html   \# Idle screensaver (included by dashboards)  
├── kiosk.sh                \# Kiosk launcher (Chromium, Wayland)  
├── SETUP.md                \# Step-by-step setup and installation  
├── kiosk-setup.md         \# Kiosk install: systemd service + restart, or script-only  
├── kiosk-debug.md          \# Step-by-step kiosk troubleshooting  
├── weather-kiosk.service   \# Systemd user service (optional)  
├── labwc-autostart         \# Autostart script that starts the service  
├── restart-kiosk.sh       \# Restart kiosk without rebooting  
└── README.md               \# You are here
```

---
## **🚀 Setup & Installation**

For full step-by-step instructions (static IP, API config, Docker install, backend launch, kiosk mode), see **[SETUP.md](SETUP.md)**.

**Quick summary:** Configure `.env` with your Weather.com API key and optional `LAT_LON`; set **location**, **Vevor on/off**, and **screensaver** in the app’s **Settings** page (gear icon). Run the app with `docker compose up -d`; use **kiosk-setup.md** for kiosk mode on the Pi.

## **Dashboard Layout**

* **Left panel:** **Inside** (temp/humidity from Home Assistant, if configured). If you enable a personal weather station in **Settings**, an **Outside** block appears below with live PWS data (temp, wind, humidity, UV).  
* **Right panel:** 3-day forecast for your location (location name and coordinates set in **Settings**).  
* **Nav:** Home, 5 Day, Controls; **Settings** (gear icon, right) for location, Vevor, and screensaver options.  
* **Refresh:** Dashboard auto-refreshes every 5 minutes (300 seconds) via HTML meta-tag. Changes in Settings apply after “Save and refresh kiosk” (no Pi reboot).

## **🛠 Troubleshooting**

* **Backend logs:** `docker logs -f pi_weather_dashboard` — API errors and missing `observations` are logged here. Use this to see Inside sensor fetch results and any HA errors.
* **Weather API "No observations":** If the dashboard shows "Weather data unavailable", check the backend logs for the API response. Often invalid API key or station ID; fix in `.env` and restart the container (`docker-compose restart`).
* **Inside sensor shows unavailable:**  
  1. **Check logs:** `docker logs pi_weather_dashboard 2>&1 | tail -50` — look for lines like `Inside sensor: temp=... humidity=...` or `Inside sensor: HA entity ... returned 404`.  
  2. **Test the HA connection:** From the Pi (or any machine that can reach the app), run:  
     `curl -s http://localhost:5000/api/debug/inside-sensor`  
     This returns JSON with the entity IDs in use, each entity’s HTTP status, raw `state` from Home Assistant, and the parsed value. If `status_code` is 404, the entity ID is wrong (check **Settings → Devices & services** or **Developer tools → States** in HA). If `state` is `"unavailable"` or `"unknown"`, the device is offline or not reporting. Fix `.env` and restart the container (`docker-compose restart`).
* **Kiosk log:** On the Pi, `cat /tmp/weather-kiosk.log` — Chromium and script output.
* **Kiosk not displaying?** Boot must be **Desktop** (or Desktop Autologin). See **kiosk-debug.md** for autostart, manual run, keyring popup, and Chromium install.  
* **Restart kiosk without reboot:** Use the systemd service (Option A in Step 3). Run `./restart-kiosk.sh` from a **terminal on the Pi desktop** (not SSH) so the restarted browser has Wayland. The script shows service status and the last 20 lines of the kiosk log.
* **Browser doesn’t relaunch after restart:** See **kiosk-setup.md** (“If the browser doesn’t relaunch after restart”). Check `cat /tmp/weather-kiosk.log` for `WAYLAND_DISPLAY` (should be set) and any errors after “Launching Chromium...”.  
* **Screen blanking:** Disable via *Raspberry Pi Configuration > Display* to keep the dashboard on 24/7.

## **🎨 Future Customization**

* Add touch buttons for "Reboot" or "Screen Off."
* Integrate Home Assistant sensors for internal Tiny House battery/solar status.

---


