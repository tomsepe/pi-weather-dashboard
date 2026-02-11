from flask import Flask, render_template
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# CONFIGURATION
STATION_ID = "KORVENET36"
API_KEY = "63fi33VZ"
LAT_LON = "44.05,-123.35"  # Veneta, OR


def _mask_key(key: str) -> str:
    """Avoid logging full API key."""
    if not key or len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


@app.route("/")
def index():
    try:
        # 1. Current conditions from your PWS (Vevor station)
        pws_url = (
            f"https://api.weather.com/v2/pws/observations/current?"
            f"stationId={STATION_ID}&format=json&units=e&apiKey={API_KEY}"
        )
        log.info("Fetching PWS current conditions (key=%s)", _mask_key(API_KEY))
        pws_resp = requests.get(pws_url, timeout=10)

        if pws_resp.status_code != 200:
            log.error(
                "PWS API returned status %s: %s",
                pws_resp.status_code,
                pws_resp.text[:500],
            )
            return _error_page(
                "PWS API error",
                f"Server returned {pws_resp.status_code}. Check docker logs for response body.",
                pws_resp.status_code,
            )

        try:
            pws_data = pws_resp.json()
        except Exception as e:
            log.error("PWS response is not JSON: %s", e)
            return _error_page(
                "Invalid API response",
                "Response was not valid JSON. Check docker logs.",
                502,
            )

        if "observations" not in pws_data:
            # API often returns {"errors": [{"message": "..."}]} or similar when key/station invalid
            errors = pws_data.get("errors", pws_data.get("error", pws_data))
            log.error(
                "PWS response missing 'observations'. Keys: %s. Body snippet: %s",
                list(pws_data.keys()),
                str(errors)[:400],
            )
            return _error_page(
                "No observations in API response",
                "The weather API did not return station data. Often caused by invalid API key or "
                "station ID, or the PWS API may have changed. Check docker logs for the exact response.",
                502,
            )

        obs_list = pws_data["observations"]
        if not obs_list:
            log.warning("PWS returned observations list empty")
            return _error_page(
                "No current observation",
                "Station returned no current observation (list empty). Check station ID and that the station is reporting.",
                502,
            )

        current = obs_list[0]

        # 2. Local forecast
        forecast_url = (
            f"https://api.weather.com/v3/wx/forecast/daily/5day?"
            f"geocode={LAT_LON}&format=json&units=e&language=en-US&apiKey={API_KEY}"
        )
        log.info("Fetching forecast")
        forecast_resp = requests.get(forecast_url, timeout=10)

        if forecast_resp.status_code != 200:
            log.error(
                "Forecast API returned status %s: %s",
                forecast_resp.status_code,
                forecast_resp.text[:500],
            )
            return _error_page(
                "Forecast API error",
                f"Forecast server returned {forecast_resp.status_code}. Check docker logs.",
                forecast_resp.status_code,
            )

        try:
            forecast = forecast_resp.json()
        except Exception as e:
            log.error("Forecast response is not JSON: %s", e)
            return _error_page("Invalid forecast response", "Not valid JSON.", 502)

        return render_template("dashboard.html", current=current, forecast=forecast)

    except requests.RequestException as e:
        log.exception("Network error calling weather APIs")
        return _error_page(
            "Network error",
            str(e) + " Check connectivity and docker logs.",
            503,
        )
    except Exception as e:
        log.exception("Unexpected error")
        return _error_page(
            "Server error",
            str(e) + " Check docker logs for full traceback.",
            500,
        )


def _error_page(title: str, detail: str, status: int = 500) -> tuple:
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background: #000; color: #fff; font-family: sans-serif; margin: 0; padding: 20px; }}
        h1 {{ color: #ff9f0a; font-size: 24px; }}
        .detail {{ color: #aaa; margin: 16px 0; max-width: 90vw; word-break: break-word; }}
        .hint {{ color: #666; font-size: 14px; margin-top: 24px; }}
    </style>
    <meta http-equiv="refresh" content="60">
</head>
<body>
    <h1>Weather data unavailable</h1>
    <p><strong>{title}</strong></p>
    <div class="detail">{detail}</div>
    <div class="hint">Run: docker logs pi_weather_dashboard</div>
    <div class="hint">Page will retry in 60 seconds.</div>
</body>
</html>
"""
    return html, status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
