import json
import os
import random
import re
from flask import Flask, render_template, request, jsonify, redirect
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# CONFIGURATION
# Get a valid PWS API key from https://www.wunderground.com/member/api-keys (or your
# weather.com developer account). 401 "Invalid apiKey" in logs means replace API_KEY below.
STATION_ID = os.environ.get("WU_STATION_ID")
API_KEY = os.environ.get("WU_API_KEY")
LAT_LON = os.environ.get("LAT_LON")

# Settings file (UI-editable; overrides/env fallbacks applied in _load_settings)
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "location_name": "Veneta",
    "latitude": None,
    "longitude": None,
    "vevor_enabled": True,
    "screensaver_enabled": True,
    "screensaver_timeout_sec": 180,
    "screensaver_type": "rainbow_ball",
}
SCREENSAVER_TYPES = ("black", "rainbow_ball", "weather_quote")


def _parse_lat_lon_from_env() -> tuple[float | None, float | None]:
    """Parse LAT_LON env (e.g. '44.05,-123.35') into (lat, lon) or (None, None)."""
    raw = (os.environ.get("LAT_LON") or "").strip().strip('"')
    if not raw:
        return None, None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def _load_settings() -> dict:
    """Load settings from config/settings.json with env/default fallbacks."""
    out = dict(DEFAULT_SETTINGS)
    env_lat, env_lon = _parse_lat_lon_from_env()
    if env_lat is not None and env_lon is not None:
        out["latitude"] = env_lat
        out["longitude"] = env_lon
    if not os.path.isfile(SETTINGS_FILE):
        return out
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Could not load settings file: %s", e)
        return out
    for key in DEFAULT_SETTINGS:
        if key in data and data[key] is not None:
            out[key] = data[key]
    if out["latitude"] is None and env_lat is not None:
        out["latitude"] = env_lat
    if out["longitude"] is None and env_lon is not None:
        out["longitude"] = env_lon
    return out


def _get_lat_lon_str() -> str:
    """Return geocode string for APIs (latitude,longitude). Uses settings then env."""
    s = _load_settings()
    lat, lon = s.get("latitude"), s.get("longitude")
    if lat is not None and lon is not None:
        return f"{lat},{lon}"
    return LAT_LON or ""


def _save_settings(data: dict) -> None:
    """Validate and write settings to config/settings.json."""
    allowed = set(DEFAULT_SETTINGS.keys())
    payload = {k: v for k, v in data.items() if k in allowed}
    for key, default in DEFAULT_SETTINGS.items():
        if key not in payload and default is not None:
            payload[key] = default
    lat = payload.get("latitude")
    lon = payload.get("longitude")
    if lat is not None:
        try:
            payload["latitude"] = float(lat)
        except (TypeError, ValueError):
            payload["latitude"] = None
    if lon is not None:
        try:
            payload["longitude"] = float(lon)
        except (TypeError, ValueError):
            payload["longitude"] = None
    timeout = payload.get("screensaver_timeout_sec", 180)
    try:
        payload["screensaver_timeout_sec"] = max(10, int(timeout))
    except (TypeError, ValueError):
        payload["screensaver_timeout_sec"] = 180
    stype = (payload.get("screensaver_type") or "").strip()
    if stype not in SCREENSAVER_TYPES:
        payload["screensaver_type"] = "rainbow_ball"
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

# Home Assistant: long-lived token at http://HA_URL/profile; token stays server-side.
HA_URL = (os.environ.get("HA_URL") or "").rstrip("/")
HA_ACCESS_TOKEN = os.environ.get("HA_ACCESS_TOKEN") or ""
# Shelly (or other) temp/humidity sensor entity IDs for "Inside" on dashboard (e.g. sensor.shelly_plus_ht_xxx_temperature).
HA_INSIDE_TEMP_ENTITY = (os.environ.get("HA_INSIDE_TEMP_ENTITY") or "").strip()
HA_INSIDE_HUMIDITY_ENTITY = (os.environ.get("HA_INSIDE_HUMIDITY_ENTITY") or "").strip()


def _ha_configured() -> bool:
    return bool(HA_URL and HA_ACCESS_TOKEN)


def _load_weather_quote() -> tuple[str, str] | None:
    """Load weather_quotes.md, parse lines, return (quote_text, author) or None."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_quotes.md")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    # Format: N. "Quote." — **Author**
    pattern = re.compile(r'^\d+\.\s*"([^"]+)"\s*[—\-]\s*\*\*([^*]+)\*\*')
    quotes = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            quotes.append((m.group(1), m.group(2).strip()))
    if not quotes:
        return None
    return random.choice(quotes)


@app.after_request
def _disable_cache_for_dashboard(response):
    """Prevent browsers from caching dashboard HTML so updates show after deploy."""
    if request.path in ("/", "/5day", "/ha", "/settings") and response.content_type and "text/html" in response.content_type:
        response.cache_control.no_store = True
        response.cache_control.no_cache = True
        response.cache_control.must_revalidate = True
        response.cache_control.max_age = 0
    return response


def _fetch_ha_state(entity_id: str) -> dict | None:
    """Fetch one entity state from HA. Returns state dict or None on error."""
    if not entity_id or not _ha_configured():
        return None
    url = f"{HA_URL}/api/states/{entity_id}"
    try:
        r = requests.get(url, headers=_ha_headers(), timeout=5)
        if r.status_code != 200:
            log.warning("Inside sensor: HA entity %s returned %s", entity_id, r.status_code)
            return None
        data = r.json()
        log.debug("Inside sensor: %s state=%s", entity_id, data.get("state"))
        return data
    except requests.RequestException as e:
        log.warning("Inside sensor: HA fetch %s failed: %s", entity_id, e)
        return None


def _parse_number(state: dict | None) -> float | None:
    """Parse state or attribute as number. state['state'] or state['attributes'].value."""
    if not state or not isinstance(state, dict):
        return None
    raw = state.get("state")
    if raw is not None and raw != "unavailable" and raw != "unknown":
        try:
            return float(raw)
        except (TypeError, ValueError):
            pass
    return None


def _fetch_inside_sensors() -> tuple[float | None, float | None]:
    """Return (inside_temp, inside_humidity) from HA entities. (None, None) if not configured or error."""
    temp_val, humidity_val = None, None
    if not HA_INSIDE_TEMP_ENTITY and not HA_INSIDE_HUMIDITY_ENTITY:
        log.debug("Inside sensor: no entity IDs configured (HA_INSIDE_TEMP_ENTITY, HA_INSIDE_HUMIDITY_ENTITY)")
        return None, None
    if HA_INSIDE_TEMP_ENTITY:
        s = _fetch_ha_state(HA_INSIDE_TEMP_ENTITY)
        temp_val = _parse_number(s)
        if temp_val is None and s is not None:
            log.info("Inside sensor: temp entity %s state=%r (unparseable or unavailable)", HA_INSIDE_TEMP_ENTITY, s.get("state"))
        # Single entity may expose humidity in attributes (e.g. Shelly Plus H&T)
        if s and not HA_INSIDE_HUMIDITY_ENTITY:
            attrs = s.get("attributes") or {}
            for key in ("humidity", "current_humidity"):
                if key in attrs and attrs[key] is not None:
                    try:
                        humidity_val = float(attrs[key])
                    except (TypeError, ValueError):
                        pass
                    break
    if HA_INSIDE_HUMIDITY_ENTITY:
        s = _fetch_ha_state(HA_INSIDE_HUMIDITY_ENTITY)
        humidity_val = _parse_number(s)
        if humidity_val is None and s is not None:
            log.info("Inside sensor: humidity entity %s state=%r (unparseable or unavailable)", HA_INSIDE_HUMIDITY_ENTITY, s.get("state"))
    log.info("Inside sensor: temp=%s humidity=%s", temp_val, humidity_val)
    return temp_val, humidity_val


def _mask_key(key: str) -> str:
    """Avoid logging full API key."""
    if not key or len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def _fetch_forecast(days: int):
    """Fetch daily forecast (5 or 10 day). Returns (forecast_dict, None) or (None, error_response)."""
    if days not in (5, 10):
        return None, _error_page("Bad request", "Invalid forecast days.", 400)
    geocode = _get_lat_lon_str()
    if not geocode or not API_KEY:
        return None, _error_page("Configuration", "Set LAT_LON (or latitude/longitude in Settings) and WU_API_KEY.", 503)
    forecast_url = (
        f"https://api.weather.com/v3/wx/forecast/daily/{days}day?"
        f"geocode={geocode}&format=json&units=e&language=en-US&apiKey={API_KEY}"
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


# Weather.com iconCode -> slug for 5-day icons (sunny, partly-cloudy, cloudy, rainy)
# Codes: 1=Sunny, 2=Mostly Sunny, 3=Partly Cloudy, 4=Intermittent Clouds, 5=Hazy, 6-8=Cloudy/Mostly/Overcast,
# 11=Fog, 12-18=Showers/Rain/T-storms, 19-26,29=Snow/Flurries/Ice/Sleet, 33-34=Clear/Mostly Clear, 35-44=night/variants
_ICON_CODE_TO_SLUG = {
    **{c: "sunny" for c in (1, 2, 33, 34, 30)},
    **{c: "partly-cloudy" for c in (3, 4, 5, 35, 36, 37)},
    **{c: "cloudy" for c in (6, 7, 8, 11, 38)},
    **{c: "rainy" for c in (12, 13, 14, 15, 16, 17, 18, 39, 40, 41, 42)},
    **{c: "snowy" for c in (19, 20, 22, 23, 24, 25, 26, 29, 43, 44)},
}


def _narrative_to_icon_slug(narrative: str | None) -> str:
    """Derive icon slug from narrative text when iconCode not available."""
    if not narrative:
        return "cloudy"
    n = narrative.lower()
    if "rain" in n or "shower" in n or "storm" in n or "thunder" in n:
        return "rainy"
    if "snow" in n or "flurr" in n or "sleet" in n or "ice" in n:
        return "snowy"
    if "sun" in n or "clear" in n:
        return "sunny"
    if "partly" in n or "partially" in n or "intermittent" in n:
        return "partly-cloudy"
    if "cloud" in n or "overcast" in n or "fog" in n or "haze" in n:
        return "cloudy"
    return "cloudy"


def _forecast_icon_slugs(forecast: dict) -> list[str]:
    """Return list of icon slugs (one per day) for the 5-day forecast."""
    days = forecast.get("dayOfWeek") or []
    narratives = forecast.get("narrative") or []
    icon_codes = forecast.get("iconCode")
    if not isinstance(icon_codes, list):
        icon_codes = None
    slugs = []
    for i in range(len(days)):
        if icon_codes and i < len(icon_codes) and icon_codes[i] is not None:
            try:
                code = int(icon_codes[i])
                slug = _ICON_CODE_TO_SLUG.get(code, "cloudy")
            except (TypeError, ValueError):
                slug = _narrative_to_icon_slug(narratives[i] if i < len(narratives) else None)
        else:
            slug = _narrative_to_icon_slug(narratives[i] if i < len(narratives) else None)
        slugs.append(slug)
    return slugs


def _fetch_current_by_geocode() -> dict | None:
    """Fetch current conditions by lat/lon (Weather.com v3). Returns PWS-shaped dict or None."""
    geocode = _get_lat_lon_str()
    if not geocode or not API_KEY:
        return None
    url = (
        f"https://api.weather.com/v3/wx/observations/current?"
        f"geocode={geocode}&units=e&language=en-US&format=json&apiKey={API_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            log.warning("Current-by-geocode API returned %s", r.status_code)
            return None
        data = r.json()
    except Exception as e:
        log.warning("Current-by-geocode request failed: %s", e)
        return None
    # v3 returns temperature, windSpeed, relativeHumidity, uvIndex (flat)
    temp = data.get("temperature")
    wind = data.get("windSpeed")
    humidity = data.get("relativeHumidity")
    uv = data.get("uvIndex")
    if temp is None:
        return None
    # Normalize to PWS-like shape for dashboard template
    return {
        "imperial": {
            "temp": temp if isinstance(temp, (int, float)) else None,
            "windSpeed": wind if isinstance(wind, (int, float)) else 0,
        },
        "humidity": humidity if isinstance(humidity, (int, float)) else None,
        "uv": uv if uv is not None else 0,
    }


def _template_settings() -> dict:
    """Settings dict to pass into every dashboard/settings template."""
    s = _load_settings()
    return {
        "location_name": s.get("location_name") or "",
        "screensaver_enabled": bool(s.get("screensaver_enabled", True)),
        "screensaver_timeout_sec": max(10, int(s.get("screensaver_timeout_sec") or 180)),
        "screensaver_type": s.get("screensaver_type") in SCREENSAVER_TYPES and s["screensaver_type"] or "rainbow_ball",
    }


def _fallback_current() -> dict:
    """Placeholder current when no PWS and no geocode current available."""
    return {
        "imperial": {"temp": None, "windSpeed": None},
        "humidity": None,
        "uv": None,
    }


@app.route("/")
def index():
    try:
        settings = _load_settings()
        vevor_enabled = bool(settings.get("vevor_enabled", True))
        current = None

        if vevor_enabled and STATION_ID and API_KEY:
            # Current conditions from PWS (Vevor station)
            pws_url = (
                f"https://api.weather.com/v2/pws/observations/current?"
                f"stationId={STATION_ID}&format=json&units=e&apiKey={API_KEY}"
            )
            log.info("Fetching PWS current conditions (key=%s)", _mask_key(API_KEY))
            pws_resp = requests.get(pws_url, timeout=10)

            if pws_resp.status_code == 200:
                try:
                    pws_data = pws_resp.json()
                    obs_list = pws_data.get("observations") or []
                    if obs_list:
                        current = obs_list[0]
                except Exception as e:
                    log.warning("PWS response parse failed: %s", e)
            if current is None:
                log.error(
                    "PWS API returned status %s: %s",
                    pws_resp.status_code,
                    (pws_resp.text[:500] if getattr(pws_resp, "text", None) else ""),
                )
                return _error_page(
                    "PWS API error",
                    f"Server returned {pws_resp.status_code}. Check docker logs or disable Vevor in Settings.",
                    pws_resp.status_code,
                )

        if current is None:
            current = _fetch_current_by_geocode()
        if current is None:
            current = _fallback_current()

        # Local forecast (5 day)
        forecast, err = _fetch_forecast(5)
        if err is not None:
            return err

        # Inside temp/humidity from Home Assistant (Shelly or other)
        inside_temp, inside_humidity = _fetch_inside_sensors()
        inside_configured = bool(HA_INSIDE_TEMP_ENTITY or HA_INSIDE_HUMIDITY_ENTITY)

        quote = _load_weather_quote()
        quote_text, quote_author = quote if quote else (None, None)
        ctx = _template_settings()
        return render_template(
            "dashboard.html",
            current=current,
            forecast=forecast,
            inside_temp=inside_temp,
            inside_humidity=inside_humidity,
            inside_configured=inside_configured,
            show_outside=vevor_enabled,
            quote_text=quote_text,
            quote_author=quote_author,
            **ctx,
        )

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
def redirect_10day_to_5day():
    """Redirect old /10day links to /5day (10-day API often returns 401 on free keys)."""
    return redirect("/5day", code=302)


@app.route("/5day")
def forecast_5day():
    try:
        forecast, err = _fetch_forecast(5)
        if err is not None:
            return err
        forecast_icons = _forecast_icon_slugs(forecast)
        quote = _load_weather_quote()
        quote_text, quote_author = quote if quote else (None, None)
        ctx = _template_settings()
        return render_template(
            "dashboard_5day.html",
            forecast=forecast,
            forecast_note=None,
            forecast_icons=forecast_icons,
            quote_text=quote_text,
            quote_author=quote_author,
            **ctx,
        )
    except Exception as e:
        log.exception("Unexpected error in 5-day forecast")
        return _error_page(
            "Server error",
            str(e) + " Check docker logs for full traceback.",
            500,
        )


# --- Debug: Inside sensor (for troubleshooting) ---


def _fetch_ha_state_debug(entity_id: str) -> dict:
    """Fetch one HA entity and return status_code, state, parsed number, and any error (for debug API)."""
    out = {"entity_id": entity_id, "status_code": None, "state": None, "parsed": None, "error": None}
    if not entity_id or not _ha_configured():
        out["error"] = "HA not configured or entity_id empty"
        return out
    url = f"{HA_URL}/api/states/{entity_id}"
    try:
        r = requests.get(url, headers=_ha_headers(), timeout=5)
        out["status_code"] = r.status_code
        if r.status_code != 200:
            out["error"] = r.text[:200] if r.text else f"HTTP {r.status_code}"
            return out
        data = r.json()
        out["state"] = data.get("state")
        out["parsed"] = _parse_number(data)
        return out
    except requests.RequestException as e:
        out["error"] = str(e)
        return out


@app.route("/api/debug/inside-sensor")
def debug_inside_sensor():
    """Return JSON with HA inside-sensor fetch details for troubleshooting. No secrets."""
    payload = {
        "configured": bool(HA_INSIDE_TEMP_ENTITY or HA_INSIDE_HUMIDITY_ENTITY),
        "ha_configured": _ha_configured(),
        "temp_entity": HA_INSIDE_TEMP_ENTITY or None,
        "humidity_entity": HA_INSIDE_HUMIDITY_ENTITY or None,
        "temp": None,
        "humidity": None,
    }
    if HA_INSIDE_TEMP_ENTITY:
        payload["temp"] = _fetch_ha_state_debug(HA_INSIDE_TEMP_ENTITY)
    if HA_INSIDE_HUMIDITY_ENTITY:
        payload["humidity"] = _fetch_ha_state_debug(HA_INSIDE_HUMIDITY_ENTITY)
    return jsonify(payload)


@app.route("/api/random-quote")
def api_random_quote():
    """Return a random weather quote for the screensaver (refreshes every 5 min client-side)."""
    quote = _load_weather_quote()
    if not quote:
        return jsonify({"quote_text": None, "quote_author": None})
    quote_text, quote_author = quote
    return jsonify({"quote_text": quote_text, "quote_author": quote_author})


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
    quote = _load_weather_quote()
    quote_text, quote_author = quote if quote else (None, None)
    ctx = _template_settings()
    return render_template(
        "dashboard_ha.html",
        ha_configured=_ha_configured(),
        quote_text=quote_text,
        quote_author=quote_author,
        **ctx,
    )


@app.route("/settings")
def settings_page():
    """Settings page: location, lat/lon, Vevor, screensaver options."""
    s = _load_settings()
    return render_template(
        "settings.html",
        location_name=s.get("location_name") or "",
        latitude=s.get("latitude"),
        longitude=s.get("longitude"),
        vevor_enabled=bool(s.get("vevor_enabled", True)),
        screensaver_enabled=bool(s.get("screensaver_enabled", True)),
        screensaver_timeout_sec=max(10, int(s.get("screensaver_timeout_sec") or 180)),
        screensaver_type=s.get("screensaver_type") in SCREENSAVER_TYPES and s["screensaver_type"] or "rainbow_ball",
    )


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    """Save settings from JSON body; return 200 or 4xx with error."""
    data = request.get_json(silent=True) or {}
    try:
        _save_settings(data)
        return jsonify({"ok": True}), 200
    except (ValueError, OSError) as e:
        log.warning("Save settings failed: %s", e)
        return jsonify({"error": str(e)}), 400


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
