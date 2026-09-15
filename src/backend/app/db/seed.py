"""
seed.py — Add ML risk scores and maintenance plan on top of the
          data team's SQLite database (src/data/output/grid_data.db).

The data pipeline (src/data/run_all.py) must be run FIRST.
This script then:
  1. Creates the 3 ML-only tables (risk_scores, shap_values, maintenance_tasks)
     in the same DB — does NOT touch the 5 data tables.
  2. Trains XGBoost on the sensor + incident data already in the DB.
  3. Computes SHAP values.
  4. Generates the maintenance plan.

Run from src/backend/:
    python -m app.db.seed
"""

import sys
import logging
from pathlib import Path

# Make sure imports resolve when run as __main__
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import inspect, text
from app.db.database import engine, SessionLocal
from app.db.models import Base, RiskScore, ShapValue, MaintenanceTask

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def _create_ml_tables():
    """
    Create ONLY the 3 ML tables in the data team's DB.
    The 5 data tables (assets, sensor_readings, etc.) already exist —
    we never touch them.
    """
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    ml_tables = {
        "risk_scores":        RiskScore,
        "shap_values":        ShapValue,
        "maintenance_tasks":  MaintenanceTask,
    }

    for table_name, model_cls in ml_tables.items():
        if table_name not in existing:
            model_cls.__table__.create(engine)
            log.info("Created table: %s", table_name)
        else:
            log.info("Table already exists (skipping): %s", table_name)


def _verify_data_tables():
    """Check the 5 required data tables exist before scoring."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    required = {"assets", "sensor_readings", "historical_incidents",
                "weather_alerts", "grid_zones"}
    missing = required - existing
    if missing:
        raise RuntimeError(
            f"Data tables missing: {missing}\n"
            "Run `python run_all.py` from src/data/ first."
        )

    # Quick row count check
    with engine.connect() as conn:
        asset_count = conn.execute(text("SELECT COUNT(*) FROM assets")).scalar()
        sensor_count = conn.execute(text("SELECT COUNT(*) FROM sensor_readings")).scalar()
    log.info("Data check: %d assets, %d sensor readings", asset_count, sensor_count)

    if asset_count == 0:
        raise RuntimeError("Assets table is empty — run src/data/run_all.py first.")


def seed():
    log.info("DB: %s", engine.url)

    # 1. Verify data team's tables exist
    _verify_data_tables()

    # 2. Create ML-only tables (non-destructive)
    _create_ml_tables()

    # 3. Run ML scoring + SHAP
    from app.services.prediction import score_all_assets
    db = SessionLocal()
    try:
        log.info("Training XGBoost model and scoring assets…")
        score_all_assets(db)

        # 4. Generate maintenance plan
        from app.services.maintenance_gen import generate_plan
        log.info("Generating maintenance plan…")
        generate_plan(db)

        log.info("✅  Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
