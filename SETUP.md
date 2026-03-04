# Pi Weather Dashboard — Setup

Step-by-step setup for the Pi Weather Dashboard: networking, API configuration, Docker, and kiosk mode.

---

## 1. Static IP (recommended)

A static IP gives faster startup and a predictable address for the Pi.

```bash
sudo nmcli device wifi list
sudo nmcli c show
sudo nmcli dev wifi connect <SSID> password <password>
```

Get the connection name (e.g. `netplan-wlan0-RR_IoT`).

### Static IP

```bash
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.addresses 192.168.30.102/24
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.gateway 192.168.30.1
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.dns 192.168.30.1
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.method manual
```

- `ipv4.addresses` — IP and subnet (e.g. /24 = 255.255.255.0)
- `ipv4.gateway` — Router IP
- `ipv4.dns` — DNS (often same as gateway)
- `ipv4.method manual` — Use static config

### DHCP (revert to automatic)

```bash
sudo nmcli connection modify "netplan-eth0" ipv4.method auto
```

### Apply changes

```bash
sudo nmcli connection up "RR_IoT"
```

Replace `RR_IoT` with your connection name.

---

## 2. API and environment configuration

You need a **Weather.com / Wunderground API key** for forecast (and optionally for PWS current conditions). Get one from [Wunderground API keys](https://www.wunderground.com/member/api-keys) or your Weather.com developer account.

**In the app:** Use the **Settings** page (gear icon in the nav) to set:

- Location city name
- Latitude and longitude (for forecast and location-based current conditions)
- Enable/disable Vevor (or other) personal weather station
- Screensaver (on/off, timeout, type: black / rainbow ball / weather quote)

Settings are stored in `config/settings.json` and apply without restarting the app.

**For Docker or first run**, create a `.env` file in the project root with defaults:

```bash
nano .env
```

Example:

```
HA_URL=http://your-home-assistant:8123
HA_ACCESS_TOKEN=your_long_lived_token
WU_API_KEY=your_weather_api_key
WU_STATION_ID=your_station_ID
LAT_LON="44.05,-123.35"

# Optional: "Inside" panel (Shelly or other HA temp/humidity)
HA_INSIDE_TEMP_ENTITY=sensor.your_shelly_temperature
HA_INSIDE_HUMIDITY_ENTITY=sensor.your_shelly_humidity
```

- **WU_API_KEY** — Required for forecast (and for PWS if you use one).
- **WU_STATION_ID** — Only if you use a personal weather station (e.g. Vevor).
- **LAT_LON** — Default latitude,longitude used until you set them in Settings.
- **HA_*** — For Home Assistant “Inside” panel and Controls page; see README for Shelly entity IDs.

---

## 3. Docker install (Pi / Debian)

Install dependencies:

```shell
sudo apt-get install -y ca-certificates curl wget gnupg lsb-release git jq vim
```

Add Docker’s GPG key and repository:

```shell
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Install Docker and Docker Compose:

```shell
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow your user to run Docker without `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

(You may need to log out and back in for the group to apply everywhere.)

---

## 4. Launch the backend

From the project directory:

```bash
cd ~/pi-weather-dashboard
docker compose up -d
```

The dashboard is available at **http://localhost:5000** (or http://\<Pi-IP\>:5000 from another device).

---

## 5. Kiosk mode (Trixie / Wayland)

On Raspberry Pi OS with **labwc**, the dashboard can start in kiosk mode (full-screen Chromium) on login.

- **Option A (recommended):** Install a systemd user service + labwc autostart so you can restart the kiosk with `./restart-kiosk.sh` without rebooting.
- **Option B:** Copy `kiosk.sh` into labwc autostart only; to restart you must log out and back in (or reboot).

**Follow the full steps and troubleshooting in [kiosk-setup.md](kiosk-setup.md)** — it covers both options, what to do if the browser doesn’t relaunch after restart, screen blanking, and Wayland.

---

## 6. After setup

- Open the dashboard in a browser and go to **Settings** (gear icon) to set location, Vevor, and screensaver.
- Use **Save and refresh kiosk** to apply settings and reload the dashboard without rebooting the Pi.
- Troubleshooting: see **README.md** (Troubleshooting) and **kiosk-debug.md** (kiosk issues).
