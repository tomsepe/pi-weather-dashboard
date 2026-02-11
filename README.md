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
├── app.py                \# Flask application logic  
├── docker-compose.yml     \# Docker service configuration  
├── Dockerfile             \# Container build instructions  
├── requirements.txt       \# Python dependencies  
├── templates/  
│   └── dashboard.html     \# 800x480 optimized UI template  
└── README.md              \# You are here

## **🚀 Setup & Installation**

### **1\. API Configuration**

Ensure you have your **Weather Underground API Key** and **Station ID**. Update the variables in app.py:

* STATION\_ID: Your Vevor station identifier.  
* API\_KEY: Your personal PWS API key.

### **2\. Launch the Backend**

Navigate to the project directory and start the Docker container:

Bash

cd \~/pi-weather-dashboard  
docker-compose up \-d

The dashboard will be available at http://localhost:5000.

### **3\. Configure Kiosk Mode (Trixie/Wayland)**

Trixie uses the **labwc** compositor. To make the dashboard launch on boot:

1. Create the autostart directory:  
   Bash  
   mkdir \-p \~/.config/labwc

2. Create/edit the autostart file: nano \~/.config/labwc/autostart  
3. Add the following script:  
   Bash  
   \#\!/bin/bash  
   sleep 8  
   chromium-browser \\  
     \--kiosk \\  
     \--noerrdialogs \\  
     \--disable-infobars \\  
     \--ozone-platform=wayland \\  
     \--window-size=800,480 \\  
     \--window-position=0,0 \\  
     http://localhost:5000 &

4. Ensure it is executable: chmod \+x \~/.config/labwc/autostart

## **🖥 Dashboard Layout**

* **Left Panel:** Real-time data from the Vevor station (Temp, Wind Speed, Humidity).  
* **Right Panel:** 3-Day forecast for Veneta, OR.  
* **Refresh Rate:** The dashboard auto-refreshes every 5 minutes (300 seconds) via HTML meta-tag.

## **🛠 Troubleshooting**

* **Logs:** View the backend logs with docker logs \-f pi\_weather\_dashboard.  
* **Network:** The dashboard uses 0.0.0.0 inside the container to allow Docker port forwarding to localhost:5000.  
* **Screen Blanking:** Disable via *Raspberry Pi Configuration \> Display* to keep the dashboard on 24/7.
* **Kiosk not displaying?** On Trixie (Wayland/labwc) the kiosk must use Chromium with \`--ozone-platform=wayland\`. Use the script in **Step 3** above in \`\~/.config/labwc/autostart\` (not a generic X11 script). Ensure the file is executable (\`chmod +x \~/.config/labwc/autostart\`) and that Docker is up before the desktop starts (the \`sleep 8\` gives the container time to be ready). You can copy the contents of \`kiosk.sh\` or follow \`kiosk-setup.md\` for the exact Wayland script. Reboot after changing autostart.

## **🎨 Future Customization**

* \[ \] Add touch buttons for "Reboot" or "Screen Off."  
* \[ \] Integrate Home Assistant sensors for internal Tiny House battery/solar status.

\---

\#\#\# Next Step  
Since you’re doing custom fabrication, would you like me to add a section to the \`README\` or the code for \*\*auto-dimming\*\* the screen at night? Since it's inside your tiny house, an 800x480 screen at full brightness might be a bit much while you're trying to sleep\!  
