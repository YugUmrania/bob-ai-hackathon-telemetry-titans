from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import MaintenanceTask
from app.models.schemas import MaintenanceTaskOut

router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


@router.get("", response_model=List[MaintenanceTaskOut])
def list_maintenance(
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    priority: Optional[str] = Query(None, description="Filter by CRITICAL|HIGH|MEDIUM|LOW"),
    status: Optional[str] = Query(None, description="Filter by scheduled|in_progress|done"),
    db: Session = Depends(get_db),
):
    """Return all maintenance tasks, ordered by scheduled_date then priority."""
    q = db.query(MaintenanceTask)

    if asset_id:
        q = q.filter(MaintenanceTask.asset_id == asset_id)
    if priority:
        q = q.filter(MaintenanceTask.priority == priority.upper())
    if status:
        q = q.filter(MaintenanceTask.status == status.lower())

    # Sort: earliest first, then CRITICAL before others
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    tasks = q.order_by(MaintenanceTask.scheduled_date.asc()).all()

    # Secondary sort by priority within each day
    tasks.sort(key=lambda t: (t.scheduled_date, priority_order.get(t.priority, 9)))

    return [MaintenanceTaskOut.model_validate(t) for t in tasks]
