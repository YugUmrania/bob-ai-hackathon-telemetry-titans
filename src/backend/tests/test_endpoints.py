"""
test_endpoints.py — Smoke tests for all API endpoints.

Uses an in-memory SQLite DB with minimal seed data so no CSV files are needed.

Run from src/backend/:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timezone

# ── In-memory test database — must be set up BEFORE importing app ─────────────

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import app AFTER engine is ready
from app.main import app                                          # noqa: E402
from app.db.database import get_db, Base                         # noqa: E402
from app.db.models import Asset, RiskScore, SensorReading, MaintenanceTask  # noqa: E402

# Override the DB dependency globally
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables on the test engine, insert seed data, yield, then drop."""
    # Create tables on the TEST engine (not the real one)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    # Asset
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

    # Risk score
    db.add(RiskScore(
        asset_id="TRF-001",
        risk_score=85.0,
        priority_score=90.0,
        risk_level="CRITICAL",
        computed_at=datetime.now(timezone.utc).isoformat(),
    ))

    # Sensor readings
    for i in range(5):
        db.add(SensorReading(
            asset_id="TRF-001",
            timestamp=f"2026-09-{10+i:02d}T12:00:00",
            temperature_c=72.0 + i,
            vibration_mm_s=3.5,
            oil_quality_index=55.0 - i,
            partial_discharge_mv=180.0 + i * 20,
        ))

    # Maintenance task
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

    # Clean up after each test
    Base.metadata.drop_all(bind=test_engine)


# ── Test client (created fresh each test via the fixture) ─────────────────────

@pytest.fixture()
def client():
    return TestClient(app)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_summary(client):
    r = client.get("/api/v1/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_assets"] == 1
    assert data["critical_count"] == 1
    assert data["maintenance_today"] >= 1


def test_list_assets(client):
    r = client.get("/api/v1/assets")
    assert r.status_code == 200
    assets = r.json()
    assert len(assets) == 1
    assert assets[0]["asset_id"] == "TRF-001"
    assert assets[0]["risk_level"] == "CRITICAL"


def test_list_assets_filter_risk_level(client):
    r = client.get("/api/v1/assets?risk_level=HIGH")
    assert r.status_code == 200
    assert r.json() == []  # no HIGH assets in test data


def test_list_assets_filter_zone(client):
    r = client.get("/api/v1/assets?zone=North")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_assets_limit(client):
    r = client.get("/api/v1/assets?limit=1")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_asset(client):
    r = client.get("/api/v1/assets/TRF-001")
    assert r.status_code == 200
    data = r.json()
    assert data["asset_id"] == "TRF-001"
    assert data["customers_served"] == 5000


def test_get_asset_not_found(client):
    r = client.get("/api/v1/assets/DOES-NOT-EXIST")
    assert r.status_code == 404


def test_sensor_readings(client):
    r = client.get("/api/v1/assets/TRF-001/sensors")
    assert r.status_code == 200
    readings = r.json()
    assert len(readings) == 5
    assert "temperature_c" in readings[0]


def test_sensor_readings_asset_not_found(client):
    r = client.get("/api/v1/assets/FAKE-999/sensors")
    assert r.status_code == 404


def test_list_maintenance(client):
    r = client.get("/api/v1/maintenance")
    assert r.status_code == 200
    tasks = r.json()
    assert len(tasks) >= 1
    assert tasks[0]["asset_id"] == "TRF-001"


def test_maintenance_filter_by_asset(client):
    r = client.get("/api/v1/maintenance?asset_id=TRF-001")
    assert r.status_code == 200
    assert all(t["asset_id"] == "TRF-001" for t in r.json())


def test_maintenance_filter_no_match(client):
    r = client.get("/api/v1/maintenance?asset_id=FAKE-000")
    assert r.status_code == 200
    assert r.json() == []
