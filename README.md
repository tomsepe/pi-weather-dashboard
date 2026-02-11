### Pi Weather Dashboard

**README.md**

Markdown

\# Tiny House Weather Dashboard  
A standalone, kiosk-mode weather station dashboard for the Raspberry Pi 4 \+ 7" Touchscreen. This project pulls real-time data from a **\*\*Vevor 7-in-1 Station\*\*** via the Weather Underground API and displays it alongside a localized forecast for **\*\*Veneta, OR\*\***.

\#\# 🛠 Tech Stack  
\* **\*\*Hardware:\*\*** Raspberry Pi 4, 7" DSI Touchscreen, Vevor PWS.  
\* **\*\*OS:\*\*** Raspberry Pi OS (Debian 13 "Trixie") using **\*\*Wayland/labwc\*\***.  
\* **\*\*Backend:\*\*** Python 3.11 (Flask) running in **\*\*Docker\*\***.  
\* **\*\*Frontend:\*\*** HTML5 / CSS Grid (Optimized for 800x480 resolution).

\#\# 📁 Project Structure  
\`\`\`text  
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

## **🚀 Setup & Installation**

### **1\. API Configuration**

Ensure you have your **Weather Underground API Key** and **Station ID**. Update the variables in app.py:

* STATION\_ID: Your Vevor station identifier.  
* API\_KEY: Your personal PWS API key.

### **2\. Launch the Backend**

Navigate to the project directory and start the Docker container:

\`\`\`bash  
cd \~/pi-weather-dashboard  
docker-compose up \-d  
\`\`\`

The dashboard will be available at http://localhost:5000.

### **3\. Configure Kiosk Mode (Trixie/Wayland)**

Trixie uses the **labwc** compositor. Full steps are in **kiosk-setup.md**. Summary:

* **Option A (recommended):** Install the **systemd user service** so you can restart the kiosk without rebooting:
  * Copy \`weather-kiosk.service\` to \`\~/.config/systemd/user/\`, run \`systemctl --user daemon-reload\`.
  * Copy \`labwc-autostart\` to \`\~/.config/labwc/autostart\` and \`chmod +x\` it.
  * Restart kiosk anytime: \`./restart-kiosk.sh\` or \`systemctl --user restart weather-kiosk.service\`.
* **Option B:** Copy \`kiosk.sh\` to \`\~/.config/labwc/autostart\` and \`chmod +x\` it (no service; no restart command).

## **🖥 Dashboard Layout**

* **Left Panel:** Real-time data from the Vevor station (Temp, Wind Speed, Humidity).  
* **Right Panel:** 3-Day forecast for Veneta, OR.  
* **Refresh Rate:** The dashboard auto-refreshes every 5 minutes (300 seconds) via HTML meta-tag.

## **🛠 Troubleshooting**

* **Backend logs:** \`docker logs -f pi_weather_dashboard\` — API errors and missing \`observations\` are logged here.  
* **Weather API / "No observations":** If the dashboard shows "Weather data unavailable", check the backend logs for the API response. Often invalid API key or station ID; fix in \`app.py\` and restart the container (\`docker-compose restart\`).  
* **Kiosk log:** On the Pi, \`cat /tmp/weather-kiosk.log\` — Chromium and script output.  
* **Kiosk not displaying?** Boot must be **Desktop** (or Desktop Autologin). See **kiosk-debug.md** for autostart, manual run, keyring popup, and Chromium install.  
* **Restart kiosk without reboot:** Use the systemd service (Option A in Step 3), then \`./restart-kiosk.sh\` or \`systemctl --user restart weather-kiosk.service\`.  
* **Screen blanking:** Disable via *Raspberry Pi Configuration \> Display* to keep the dashboard on 24/7.

## **🎨 Future Customization**

* \[ \] Add touch buttons for "Reboot" or "Screen Off."  
* \[ \] Integrate Home Assistant sensors for internal Tiny House battery/solar status.

\---

\#\#\# Next Step  
Since you’re doing custom fabrication, would you like me to add a section to the \`README\` or the code for \*\*auto-dimming\*\* the screen at night? Since it's inside your tiny house, an 800x480 screen at full brightness might be a bit much while you're trying to sleep\!  
