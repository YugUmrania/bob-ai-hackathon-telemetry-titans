"""
conftest.py — Patches the database engine to use in-memory SQLite
before any app module is imported, so all tests run without needing
real CSV data or a real database file.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── 1. Create test engine FIRST ───────────────────────────────────────────────
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ── 2. Patch app.db.database before importing app ────────────────────────────
import app.db.database as _db_module          # noqa: E402

_db_module.engine = test_engine
_db_module.SessionLocal = TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 3. Now import app (uses patched engine) ───────────────────────────────────
from app.main import app                       # noqa: E402
from app.db.database import get_db, Base       # noqa: E402
from app.db.models import (                    # noqa: E402
    Asset, RiskScore, SensorReading, MaintenanceTask,
)

app.dependency_overrides[get_db] = override_get_db


# ── 4. Per-test fixture: create tables, seed, yield, drop ────────────────────
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    from datetime import date, datetime, timezone

    db.add(Asset(
        asset_id="TRF-001",
        asset_type="transformer",
        zone="North",
        lat=40.71,
        lng=-74.01,
        customers_served=5000,
        has_critical_facility=1,
        install_year=2005,
    ))
    db.flush()

    db.add(RiskScore(
        asset_id="TRF-001",
        risk_score=85.0,
        priority_score=90.0,
        risk_level="CRITICAL",
        computed_at=datetime.now(timezone.utc).isoformat(),
    ))

    for i in range(5):
        db.add(SensorReading(
            asset_id="TRF-001",
            timestamp=f"2026-09-{10+i:02d}T12:00:00",
            temperature_c=72.0 + i,
            vibration_mm_s=3.5,
            oil_quality_index=55.0 - i,
            partial_discharge_mv=180.0 + i * 20,
        ))

    db.add(MaintenanceTask(
        task_id="TASK-001",
        asset_id="TRF-001",
        scheduled_date=date.today().isoformat(),
        action="Emergency Inspection",
        crew="Crew Alpha",
        priority="CRITICAL",
        status="scheduled",
    ))

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)
