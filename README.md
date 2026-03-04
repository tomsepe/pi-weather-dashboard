### Pi Weather Dashboard

**README.md**

# Tiny House Weather Dashboard  
A standalone, kiosk-mode weather station dashboard for the Raspberry Pi 4 & 7" Touchscreen. This project pulls real-time data from a ****Vevor 7-in-1 Station**** via the Weather Underground API and displays it alongside a localized forecast for ****Veneta, OR****.

## 🛠 Tech Stack  
* ****Hardware:**** Raspberry Pi 4, 7" DSI Touchscreen, Vevor PWS.  
* ****OS:**** Raspberry Pi OS (Debian 13 "Trixie") using ****Wayland/labwc****.  
* ****Backend:**** Python 3.11 (Flask) running in ****Docker****.  
* ****Frontend:**** HTML5 / CSS Grid (Optimized for 800x480 resolution).

## 📁 Project Structure  
```text  
pi-weather-dashboard/  
├── app.py                  \# Flask application logic  
├── docker-compose.yaml     \# Docker service configuration  
├── Dockerfile              \# Container build instructions  
├── requirements.txt        \# Python dependencies  
├── templates/  
│   └── dashboard.html       \# 800x480 optimized UI template  
├── kiosk.sh                \# Kiosk launcher (Chromium, Wayland)  
├── kiosk-setup.md           \# Kiosk install: systemd service + restart, or script-only  
├── kiosk-debug.md           \# Step-by-step kiosk troubleshooting  
├── weather-kiosk.service   \# Systemd user service (optional)  
├── labwc-autostart          \# Autostart script that starts the service  
├── restart-kiosk.sh        \# Restart kiosk without rebooting  
└── README.md                \# You are here
```

---
## **2. Setup Static IP for Networking:**
Recomend this as it makes for a faster startup and you always know how to get to your pi.

```BASH
sudo nmcli device wifi list
sudo nmcli c show
sudo nmcli dev wifi connect <SSID> password <password>
```

Get the network device name, i.e  "RR_IoT" "RR_Home"

### For static IP:
```BASH
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.addresses 192.168.30.102/24
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.gateway 192.168.30.1
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.dns 192.168.30.1
sudo nmcli connection modify "netplan-wlan0-RR_IoT" ipv4.method manual
```

### For DHCP:
```BASH
sudo nmcli connection modify "netplan-eth0" ipv4.method auto
```

ipv4.addresses Assigns the static IP you want, with the subnet mask 255.255.255.0/24
ipv4.gateway Your router’s IP address
ipv4.dns Points to the DNS server often the same as your gateway
ipv4.method manual Tells NetworkManager to use a static config instead of DHCP

### Apply the Changes:

nmcli commands modify the config, but they don't always force the network card to "reread" them immediately. You need to restart the connection.

Run this command:
```bash
sudo nmcli connection up "RR_IoT"
```

## **🚀 Setup & Installation**

### **1. API Configuration**

Ensure you have your **Weather Underground API Key** and **Station ID**. Update the variables in app.py:

* STATION_ID: Your Vevor station identifier.  
* API_KEY: Your personal PWS API key.

```BASH
nano .env
```
Configure your api, weatherstaion id, lat and lon, and your home assistant access info

```
HA_URL=http:url_of_home_assistant_server:PORT
HA_ACCESS_TOKEN=your_token
WU_API_KEY=your_api_key
WU_STATION_ID=your_station_ID
LAT_LON="44.05,-123.35"

# Optional: "Inside" panel (Shelly temp/humidity or other HA sensor)
HA_INSIDE_TEMP_ENTITY=sensor.your_shelly_temperature
HA_INSIDE_HUMIDITY_ENTITY=sensor.your_shelly_humidity
```

**Finding Shelly entity IDs:** In Home Assistant go to **Settings → Devices & services → Shelly** (or **Entities**), find your temperature/humidity device, and copy the entity IDs (e.g. `sensor.shelly_plus_ht_xxxx_temperature`, `sensor.shelly_plus_ht_xxxx_humidity`). Some devices expose one entity with both attributes—use that entity for both vars if needed.

---
## A) Docker Compose (recommended):

[](https://github.com/tomsepe/linux-voice-assistant/blob/pi4-trixie/docs/install_application.md#a-docker-compose-recommended)

Install packages:

```shell
sudo apt-get install -y ca-certificates curl wget gnupg lsb-release git jq vim
```

Download and add Docker's official GPG key:

```shell
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

Set up the Docker repository:

```BASH
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

To run Docker commands without using `sudo` every time, add your user to the `docker` group.

1. **Add your user to the group:**
```bash
sudo usermod -aG docker $USER
```

1. **Activate the changes:** You usually need to log out and log back in for this to take effect. However, you can apply the changes to your current terminal session immediately by running:

```bash
newgrp docker
```


### **2. Launch the Backend**

Navigate to the project directory and start the Docker container:

```bash  
cd ~/pi-weather-dashboard  
docker compose up -d  
```

The dashboard will be available at http://localhost:5000.

### **3. Configure Kiosk Mode (Trixie/Wayland)**

Trixie uses the **labwc** compositor. Full details are in **kiosk-setup.md**. Follow one option below (run all commands from `~/pi-weather-dashboard`).

**Option A (recommended)** — systemd user service so you can restart the kiosk without rebooting:

1. Create the systemd user config directory and install the service:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp weather-kiosk.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   ```
2. Create the labwc config directory and install the autostart script:
   ```bash
   mkdir -p ~/.config/labwc
   cp labwc-autostart ~/.config/labwc/autostart
   chmod +x ~/.config/labwc/autostart
   ```
3. Reboot (or log out and back in) so the kiosk starts on login. After that, restart anytime with:
   ```bash
   ./restart-kiosk.sh
   ```
   or `systemctl --user restart weather-kiosk.service`.

**Option B** — script-only autostart (no service; to restart you must log out and back in or reboot):

1. Create the labwc config directory and install the kiosk script:
   ```bash
   mkdir -p ~/.config/labwc
   cp kiosk.sh ~/.config/labwc/autostart
   chmod +x ~/.config/labwc/autostart
   ```
2. Reboot (or log out and back in) for the kiosk to start on login.

## **Dashboard Layout**

* **Left Panel:** Real-time data from the Vevor station (Temp, Wind Speed, Humidity).  
* **Right Panel:** 3-Day forecast for Veneta, OR.  
* **Refresh Rate:** The dashboard auto-refreshes every 5 minutes (300 seconds) via HTML meta-tag.

## **🛠 Troubleshooting**

* **Backend logs:** `docker logs -f pi_weather_dashboard` — API errors and missing `observations` are logged here.  
* **Weather API "No observations":** If the dashboard shows "Weather data unavailable", check the backend logs for the API response. Often invalid API key or station ID; fix in `app.py` and restart the container (`docker-compose restart`).  
* **Kiosk log:** On the Pi, `cat /tmp/weather-kiosk.log` — Chromium and script output.  
* **Kiosk not displaying?** Boot must be **Desktop** (or Desktop Autologin). See **kiosk-debug.md** for autostart, manual run, keyring popup, and Chromium install.  
* **Restart kiosk without reboot:** Use the systemd service (Option A in Step 3). Run `./restart-kiosk.sh` from a **terminal on the Pi desktop** (not SSH) so the restarted browser has Wayland. The script shows service status and the last 20 lines of the kiosk log.
* **Browser doesn’t relaunch after restart:** See **kiosk-setup.md** (“If the browser doesn’t relaunch after restart”). Check `cat /tmp/weather-kiosk.log` for `WAYLAND_DISPLAY` (should be set) and any errors after “Launching Chromium...”.  
* **Screen blanking:** Disable via *Raspberry Pi Configuration > Display* to keep the dashboard on 24/7.

## **🎨 Future Customization**

* Add touch buttons for "Reboot" or "Screen Off."
* Integrate Home Assistant sensors for internal Tiny House battery/solar status.

---


