from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db
from app.db.models import WeatherAlert
from app.models.schemas import WeatherAlertOut

router = APIRouter(prefix="/api/v1/weather", tags=["weather"])


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
