"""
live_weather.py — Live OpenWeatherMap alerts for any selected Indian area.

Given a state/union-territory name, build 5 grid zones around its capital
center (North / South / East / West / Central) and fetch the free
5-day / 3-hour forecast for each zone center. Consecutive severe slots are
grouped into alert events, one row per event — same shape as the data
team's weather_alerts.csv.

Endpoints provided by app/routers/weather.py:
    GET /api/v1/weather/areas            -> list of selectable areas
    GET /api/v1/weather/live?area=Maharashtra -> live alerts for that area
"""

from __future__ import annotations

import requests
from datetime import datetime, timedelta
from typing import Optional

# ── Selectable Indian areas (state -> capital center) ─────────────────────────
INDIAN_AREAS: dict[str, dict[str, float]] = {
    "Delhi NCR":         {"lat": 28.6139, "lng": 77.2090},
    "Maharashtra":       {"lat": 19.0760, "lng": 72.8777},   # Mumbai
    "Karnataka":         {"lat": 12.9716, "lng": 77.5946},   # Bengaluru
    "Tamil Nadu":        {"lat": 13.0827, "lng": 80.2707},   # Chennai
    "Telangana":         {"lat": 17.3850, "lng": 78.4867},   # Hyderabad
    "West Bengal":       {"lat": 22.5726, "lng": 88.3639},   # Kolkata
    "Gujarat":           {"lat": 23.0225, "lng": 72.5714},   # Ahmedabad
    "Rajasthan":         {"lat": 26.9124, "lng": 75.7873},   # Jaipur
    "Uttar Pradesh":     {"lat": 26.8467, "lng": 80.9462},   # Lucknow
    "Madhya Pradesh":    {"lat": 23.2599, "lng": 77.4126},   # Bhopal
    "Punjab":            {"lat": 30.7333, "lng": 76.7794},   # Chandigarh
    "Haryana":           {"lat": 29.0588, "lng": 76.0856},   # Rohtak
    "Kerala":            {"lat": 9.9312,  "lng": 76.2673},   # Kochi
    "Odisha":            {"lat": 20.2961, "lng": 85.8245},   # Bhubaneswar
    "Assam":             {"lat": 26.2006, "lng": 92.9376},   # Guwahati
    "Bihar":             {"lat": 25.5941, "lng": 85.1376},   # Patna
    "Chhattisgarh":      {"lat": 21.2514, "lng": 81.6296},   # Raipur
    "Jharkhand":         {"lat": 23.3441, "lng": 85.3096},   # Ranchi
}

ZONE_NAMES = ["North", "South", "East", "West", "Central"]
ZONE_SPREAD = {"lat": 0.15, "lng": 0.20}  # ~15 km latitude, ~20 km longitude

FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# ── Classification thresholds (mirror src/data/fetch_weather.py) ──────────────
WIND_THRESHOLDS = [
    (120, "storm",     "CRITICAL"),
    (90,  "storm",     "HIGH"),
    (60,  "high_wind", "HIGH"),
    (40,  "high_wind", "MEDIUM"),
]
HEAT_THRESHOLDS = [
    (45, "heatwave", "CRITICAL"),
    (42, "heatwave", "HIGH"),
    (38, "heatwave", "MEDIUM"),
]
PRECIP_THRESHOLDS = [
    (60, "flood", "CRITICAL"),
    (35, "flood", "HIGH"),
    (15, "storm", "MEDIUM"),
    (4,  "storm", "LOW"),
]
OWM_ID_MAP = [
    (range(200, 233), "storm",     "HIGH"),
    (range(300, 322), "storm",     "LOW"),
    (range(500, 532), "storm",     "MEDIUM"),
    (range(600, 623), "ice_storm", "HIGH"),
    (range(900, 902), "storm",     "CRITICAL"),
    (range(771, 772), "storm",     "HIGH"),
]
SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def list_areas() -> list[dict[str, str]]:
    """Return the selectable areas (name + display label)."""
    return [
        {"name": name, "region_label": f"{name} Grid"}
        for name in INDIAN_AREAS
    ]


def get_zone_centers(lat: float, lng: float) -> dict[str, tuple[float, float]]:
    """Spread 5 zone centers around the given area center."""
    dlat = ZONE_SPREAD["lat"]
    dlng = ZONE_SPREAD["lng"]
    return {
        "North":   (lat + dlat, lng),
        "South":   (lat - dlat, lng),
        "East":    (lat, lng + dlng),
        "West":    (lat, lng - dlng),
        "Central": (lat, lng),
    }


def _classify_slot(slot: dict) -> tuple[Optional[str], Optional[str], float, float, float]:
    weather_id = slot["weather"][0]["id"]
    wind_kmh   = slot.get("wind", {}).get("speed", 0) * 3.6
    temp_c     = slot["main"]["temp"] - 273.15
    precip_mm  = slot.get("rain", {}).get("3h", 0) + slot.get("snow", {}).get("3h", 0)

    alert_type = None
    severity   = None

    for id_range, atype, sev in OWM_ID_MAP:
        if weather_id in id_range:
            alert_type, severity = atype, sev
            break

    for threshold, atype, sev in WIND_THRESHOLDS:
        if wind_kmh >= threshold and (severity is None or SEVERITY_RANK[sev] > SEVERITY_RANK[severity]):
            alert_type, severity = atype, sev
        if wind_kmh >= threshold:
            break

    for threshold, atype, sev in HEAT_THRESHOLDS:
        if temp_c >= threshold and (severity is None or SEVERITY_RANK[sev] > SEVERITY_RANK[severity]):
            alert_type, severity = atype, sev
        if temp_c >= threshold:
            break

    for threshold, atype, sev in PRECIP_THRESHOLDS:
        if precip_mm >= threshold and (severity is None or SEVERITY_RANK[sev] > SEVERITY_RANK[severity]):
            alert_type, severity = atype, sev
        if precip_mm >= threshold:
            break

    return alert_type, severity, round(wind_kmh, 1), round(temp_c, 1), round(precip_mm, 1)


def _group_into_events(slots: list[dict], zone: str) -> list[dict]:
    events = []
    i = 0
    while i < len(slots):
        slot = slots[i]
        atype, sev, wind, temp, precip = _classify_slot(slot)
        if atype is None:
            i += 1
            continue

        event_start = slot["dt_txt"]
        event_end   = slot["dt_txt"]
        max_wind, max_temp, max_precip = wind, temp, precip
        peak_sev, peak_type = sev, atype

        j = i + 1
        while j < len(slots):
            next_atype, next_sev, nw, nt, np_ = _classify_slot(slots[j])
            if next_atype is None:
                break
            event_end = slots[j]["dt_txt"]
            max_wind   = max(max_wind, nw)
            max_temp   = max(max_temp, nt)
            max_precip = max(max_precip, np_)
            if SEVERITY_RANK[next_sev] > SEVERITY_RANK[peak_sev]:
                peak_sev, peak_type = next_sev, next_atype
            j += 1

        start_iso = event_start.replace(" ", "T")
        end_dt = datetime.strptime(event_end, "%Y-%m-%d %H:%M:%S")
        end_iso = (end_dt + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")

        events.append({
            "zone":            zone,
            "alert_type":      peak_type,
            "severity":        peak_sev,
            "start_time":      start_iso,
            "end_time":        end_iso,
            "max_wind_kmh":    max_wind if max_wind > 0 else None,
            "max_temp_c":      max_temp if peak_type == "heatwave" else None,
            "precipitation_mm": max_precip if max_precip > 0 else None,
            "source":          "OpenWeatherMap",
        })
        i = j
    return events


def fetch_live_alerts(area: str, api_key: str, timeout: int = 10) -> list[dict]:
    """Return live OWM alert events for the 5 zones of the selected area."""
    center = INDIAN_AREAS.get(area)
    if center is None:
        return []
    if not api_key:
        return []

    zone_centers = get_zone_centers(center["lat"], center["lng"])
    all_events = []
    counter = 0

    for zone, (lat, lng) in zone_centers.items():
        try:
            resp = requests.get(
                FORECAST_URL,
                params={"lat": lat, "lon": lng, "appid": api_key, "cnt": 40},
                timeout=timeout,
            )
            resp.raise_for_status()
        except requests.RequestException:
            continue

        slots = resp.json().get("list", [])
        events = _group_into_events(slots, zone)
        for ev in events:
            counter += 1
            ev["alert_id"] = f"WX-{counter:04d}"
        all_events.extend(events)

    return all_events