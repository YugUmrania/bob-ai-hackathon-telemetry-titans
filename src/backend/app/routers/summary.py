from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import RiskScore, MaintenanceTask
from app.models.schemas import SummaryOut

router = APIRouter(prefix="/api/v1/summary", tags=["summary"])


@router.get("", response_model=SummaryOut)
def get_summary(db: Session = Depends(get_db)):
    """Return grid-wide KPI counts for the dashboard header cards."""

    total = db.query(func.count(RiskScore.asset_id)).scalar() or 0

    critical = (
        db.query(func.count(RiskScore.asset_id))
        .filter(RiskScore.risk_level == "CRITICAL")
        .scalar() or 0
    )
    high = (
        db.query(func.count(RiskScore.asset_id))
        .filter(RiskScore.risk_level == "HIGH")
        .scalar() or 0
    )
    medium = (
        db.query(func.count(RiskScore.asset_id))
        .filter(RiskScore.risk_level == "MEDIUM")
        .scalar() or 0
    )
    low = (
        db.query(func.count(RiskScore.asset_id))
        .filter(RiskScore.risk_level == "LOW")
        .scalar() or 0
    )

    today_str = date.today().isoformat()
    maintenance_today = (
        db.query(func.count(MaintenanceTask.task_id))
        .filter(MaintenanceTask.scheduled_date == today_str)
        .scalar() or 0
    )

    # Last computed_at from risk_scores table
    last_updated_row = db.query(RiskScore.computed_at).first()
    last_updated = last_updated_row[0] if last_updated_row else today_str

    return SummaryOut(
        total_assets=total,
        critical_count=critical,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        maintenance_today=maintenance_today,
        last_updated=last_updated,
    )
