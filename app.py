import os
from flask import Flask, render_template, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# CONFIGURATION
# Get a valid PWS API key from https://www.wunderground.com/member/api-keys (or your
# weather.com developer account). 401 "Invalid apiKey" in logs means replace API_KEY below.
STATION_ID = "KORVENET36"
API_KEY = "5eb5da180a394e26b5da180a397e267f"  # Replace with your valid key
LAT_LON = "44.05,-123.35"  # Veneta, OR

# Home Assistant: long-lived token at http://HA_URL/profile; token stays server-side.
HA_URL = (os.environ.get("HA_URL") or "").rstrip("/")
HA_ACCESS_TOKEN = os.environ.get("HA_ACCESS_TOKEN") or ""


def _ha_configured() -> bool:
    return bool(HA_URL and HA_ACCESS_TOKEN)


def _mask_key(key: str) -> str:
    """Avoid logging full API key."""
    if not key or len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def _fetch_forecast(days: int):
    """Fetch daily forecast (5 or 10 day). Returns (forecast_dict, None) or (None, error_response)."""
    if days not in (5, 10):
        return None, _error_page("Bad request", "Invalid forecast days.", 400)
    forecast_url = (
        f"https://api.weather.com/v3/wx/forecast/daily/{days}day?"
        f"geocode={LAT_LON}&format=json&units=e&language=en-US&apiKey={API_KEY}"
    )
    log.info("Fetching %d-day forecast", days)
    resp = requests.get(forecast_url, timeout=10)
    if resp.status_code != 200:
        log.error("Forecast API returned status %s: %s", resp.status_code, resp.text[:500])
        return None, _error_page(
            "Forecast API error",
            f"Server returned {resp.status_code}. Check docker logs.",
            resp.status_code,
        )
    try:
        forecast = resp.json()
    except Exception as e:
        log.error("Forecast response is not JSON: %s", e)
        return None, _error_page("Invalid forecast response", "Not valid JSON.", 502)
    if "dayOfWeek" not in forecast and isinstance(forecast, dict):
        for key in ("daily", "forecast", "daypart"):
            if key in forecast and isinstance(forecast[key], dict):
                forecast = forecast[key]
                break
    if "calendarDayTemperatureMax" not in forecast:
        log.error(
            "Forecast missing expected keys. Top-level keys: %s",
            list(forecast.keys()) if isinstance(forecast, dict) else type(forecast).__name__,
        )
        return None, _error_page(
            "Unexpected forecast format",
            "API response shape changed. Check docker logs.",
            502,
        )
    return forecast, None


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

        # 2. Local forecast (5 day)
        forecast, err = _fetch_forecast(5)
        if err is not None:
            return err

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


@app.route("/10day")
def forecast_10day():
    try:
        forecast, err = _fetch_forecast(10)
        if err is not None:
            # 401/403 often means the API key doesn't include 10-day; fall back to 5-day
            if hasattr(err, "__getitem__") and err[1] in (401, 403):
                log.warning("10-day forecast not allowed (401/403). Falling back to 5-day.")
                forecast, err = _fetch_forecast(5)
                if err is not None:
                    return err
                return render_template(
                    "dashboard_10day.html",
                    forecast=forecast,
                    forecast_note="Your API plan includes 5-day forecast. Showing 5 days.",
                )
            return err
        return render_template("dashboard_10day.html", forecast=forecast, forecast_note=None)
    except Exception as e:
        log.exception("Unexpected error in 10-day forecast")
        return _error_page(
            "Server error",
            str(e) + " Check docker logs for full traceback.",
            500,
        )


# --- Home Assistant proxy (token never sent to browser) ---

def _ha_headers():
    return {
        "Authorization": f"Bearer {HA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


@app.route("/api/ha/states")
def ha_states():
    """Proxy GET /api/states from HA; optional ?domain=light,switch to filter."""
    if not _ha_configured():
        return jsonify({"error": "HA not configured"}), 503
    url = f"{HA_URL}/api/states"
    try:
        r = requests.get(url, headers=_ha_headers(), timeout=10)
        r.raise_for_status()
        states = r.json()
        if not isinstance(states, list):
            return jsonify({"error": "Unexpected HA response"}), 502
        domains = request.args.get("domain")
        if domains:
            allowed = {d.strip().lower() for d in domains.split(",") if d.strip()}
            states = [s for s in states if s.get("entity_id", "").split(".")[0] in allowed]
        return jsonify(states)
    except requests.RequestException as e:
        log.exception("HA states request failed")
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        log.exception("HA states error")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ha/service", methods=["POST"])
def ha_service():
    """Proxy POST to HA /api/services/<domain>/<service> with JSON body."""
    if not _ha_configured():
        return jsonify({"error": "HA not configured"}), 503
    data = request.get_json(silent=True) or {}
    domain = (data.get("domain") or "").strip()
    service = (data.get("service") or "").strip()
    body = data.get("data") or {}
    if not domain or not service:
        return jsonify({"error": "domain and service required"}), 400
    url = f"{HA_URL}/api/services/{domain}/{service}"
    try:
        r = requests.post(url, headers=_ha_headers(), json=body, timeout=10)
        if r.status_code >= 400:
            log.warning("HA service %s/%s returned %s: %s", domain, service, r.status_code, r.text[:200])
            return jsonify({"error": r.text or f"HA returned {r.status_code}"}), r.status_code
        try:
            body = r.json() if r.content else {}
        except ValueError:
            body = {}
        return jsonify(body), r.status_code
    except requests.RequestException as e:
        log.exception("HA service request failed")
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        log.exception("HA service error")
        return jsonify({"error": str(e)}), 500


@app.route("/ha")
def ha_dashboard():
    """Third page: Home Assistant controls. Token not in template."""
    return render_template(
        "dashboard_ha.html",
        ha_configured=_ha_configured(),
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
