from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db
from app.db.models import WeatherAlert
from app.models.schemas import WeatherAlertOut
from app.config import settings
from app.services import live_weather

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


@router.get("/areas", response_model=List[dict])
def list_areas():
    """Return the selectable Indian areas for live weather."""
    return live_weather.list_areas()


@router.get("/live", response_model=List[WeatherAlertOut])
def live_weather_alerts(
    area: str = Query(..., description="Indian state/area name, e.g. Maharashtra"),
):
    """Fetch LIVE OpenWeatherMap alerts for the 5 zones around the chosen area."""
    alerts = live_weather.fetch_live_alerts(area, settings.openweathermap_api_key)
    return [
        WeatherAlertOut(
            id=i + 1,
            zone=a["zone"],
            alert_type=a["alert_type"],
            severity=a["severity"],
            start_time=a["start_time"],
            end_time=a["end_time"],
            max_wind_kmh=a.get("max_wind_kmh"),
            max_temp_c=a.get("max_temp_c"),
            precipitation_mm=a.get("precipitation_mm"),
        )
        for i, a in enumerate(alerts)
    ]


@router.get("", response_model=List[WeatherAlertOut])
def list_weather_alerts(
    zone: Optional[str] = Query(None, description="Filter by zone"),
    severity: Optional[str] = Query(None, description="Filter by CRITICAL|HIGH|MEDIUM|LOW"),
    active_only: bool = Query(False, description="Only return currently active alerts"),
    db: Session = Depends(get_db),
):
    """Return weather alerts. Use active_only=true to get only ongoing alerts."""
    q = db.query(WeatherAlert)

    if zone:
        q = q.filter(WeatherAlert.zone == zone)
    if severity:
        q = q.filter(WeatherAlert.severity == severity.upper())
    if active_only:
        now = datetime.now(timezone.utc).isoformat()
        q = q.filter(
            WeatherAlert.start_time <= now,
        ).filter(
            (WeatherAlert.end_time == None) | (WeatherAlert.end_time >= now)  # noqa: E711
        )

    alerts = q.order_by(WeatherAlert.start_time.desc()).all()
    return [WeatherAlertOut.model_validate(a) for a in alerts]
