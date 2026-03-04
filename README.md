# Pi Weather Dashboard

A standalone, kiosk-mode weather dashboard for the Raspberry Pi 4 & 7" Touchscreen, with **optional Home Assistant integration** for inside sensors and smart-home controls. Choose your location (city name, latitude/longitude) in the in-app **Settings** page. Optionally use a **Vevor 7-in-1** (or other) personal weather station for live “Outside” conditions via the Weather Underground API; otherwise the app uses location-based current conditions and forecast from the same API.

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

- **[SETUP.md](SETUP.md)** — Full step-by-step instructions: static IP, API config, Docker install, backend launch, and kiosk overview.
- **[kiosk-setup.md](kiosk-setup.md)** — Kiosk install on the Pi: systemd service + labwc autostart, or script-only; restart without reboot.

**Quick summary:** Configure `.env` with your Weather.com API key and optional `LAT_LON`; set **location**, **Vevor on/off**, and **screensaver** in the app’s **Settings** page (gear icon). Run the app with `docker compose up -d`; then follow **kiosk-setup.md** for kiosk mode on the Pi.

## **Dashboard Layout**

* **Left panel:** **Inside** (temp/humidity from Home Assistant, if configured). If you enable a personal weather station in **Settings**, an **Outside** block appears below with live PWS data (temp, wind, humidity, UV).  
* **Right panel:** 3-day forecast for your location (location name and coordinates set in **Settings**).  
* **Nav:** Home, 5 Day, Controls; **Settings** (gear icon, right) for location, Vevor, and screensaver options.  
* **Refresh:** Dashboard auto-refreshes every 5 minutes (300 seconds) via HTML meta-tag. Changes in Settings apply after “Save and refresh kiosk” (no Pi reboot).

## **🛠 Troubleshooting**

For step-by-step kiosk and backend debugging (blank screen, browser won't start, stale data, "Weather data unavailable", Inside sensor, Wayland, logs), see **[kiosk-debug.md](kiosk-debug.md)**.

## **🎨 Future Customization**

* Add touch buttons for "Reboot" or "Screen Off."
* Integrate Home Assistant sensors for battery/solar status.

---


