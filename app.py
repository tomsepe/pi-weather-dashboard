from flask import Flask, render_template
import requests

app = Flask(__name__)

# CONFIGURATION
STATION_ID = "KORVENET36"
API_KEY = "63fi33VZ"
LAT_LON = "44.05,-123.35" # Veneta, OR

@app.route('/')
def index():
    try:
        # 1. Current Conditions from your Vevor Station
        pws_url = f"https://api.weather.com/v2/pws/observations/current?stationId={STATION_ID}&format=json&units=e&apiKey={API_KEY}"
        pws_resp = requests.get(pws_url).json()
        current = pws_resp['observations'][0]

        # 2. Local Forecast
        forecast_url = f"https://api.weather.com/v3/wx/forecast/daily/5day?geocode={LAT_LON}&format=json&units=e&language=en-US&apiKey={API_KEY}"
        forecast = requests.get(forecast_url).json()

        return render_template('dashboard.html', current=current, forecast=forecast)
    except Exception as e:
        return f"<body style='background:black;color:white;'>Updating weather data... (Error: {e})</body>", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
