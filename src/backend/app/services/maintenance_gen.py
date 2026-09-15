"""
maintenance_gen.py — Auto-generate a prioritised maintenance + crew plan.

Called by seed.py after risk scores are computed.
"""

import uuid
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.db.models import Asset, RiskScore, MaintenanceTask

log = logging.getLogger(__name__)

CREWS = ["Crew Alpha", "Crew Bravo", "Crew Charlie", "Crew Delta"]

ACTION_MAP = {
    "CRITICAL": "Emergency Inspection & Repair",
    "HIGH":     "Detailed Inspection",
    "MEDIUM":   "Routine Inspection",
    "LOW":      "Scheduled Maintenance",
}


def generate_plan(db: Session):
    """
    Generate one MaintenanceTask per CRITICAL/HIGH asset and
    one per MEDIUM/LOW asset (lower urgency, scheduled further out).
    Clears existing tasks before re-generating.
    """
    db.query(MaintenanceTask).delete()
    db.commit()

    # Fetch all risk scores ordered by priority descending
    scores = (
        db.query(RiskScore, Asset)
        .join(Asset, RiskScore.asset_id == Asset.asset_id)
        .order_by(RiskScore.priority_score.desc())
        .all()
    )

    today = date.today()
    tasks = []
    crew_day_load: dict[str, int] = {c: 0 for c in CREWS}

    for rank, (rs, asset) in enumerate(scores):
        # Schedule: CRITICAL on day 1, HIGH day 2-3, MEDIUM day 4-7, LOW day 8-14
        if rs.risk_level == "CRITICAL":
            delta = 0
        elif rs.risk_level == "HIGH":
            delta = 1 + (rank % 2)
        elif rs.risk_level == "MEDIUM":
            delta = 3 + (rank % 4)
        else:
            delta = 7 + (rank % 7)

        sched_date = today + timedelta(days=delta)

        # Assign crew with lightest load
        crew = min(crew_day_load, key=lambda c: crew_day_load[c])
        crew_day_load[crew] += 1

        action = ACTION_MAP.get(rs.risk_level, "Inspection")

        tasks.append(MaintenanceTask(
            task_id=str(uuid.uuid4()),
            asset_id=asset.asset_id,
            scheduled_date=sched_date.isoformat(),
            action=action,
            crew=crew,
            priority=rs.risk_level,
            status="scheduled",
        ))

    db.bulk_save_objects(tasks)
    db.commit()
    log.info("Generated %d maintenance tasks", len(tasks))
