from pydantic import BaseModel
from typing import Optional, List


# ── Shared ────────────────────────────────────────────────────────────────────

class ShapValueOut(BaseModel):
    feature: str
    contribution: float

    model_config = {"from_attributes": True}


# ── Asset ─────────────────────────────────────────────────────────────────────

class AssetOut(BaseModel):
    # Primary fields — match frontend types/index.ts
    asset_id: str
    id: str                      # alias for frontend (same as asset_id)
    name: str                    # e.g. "TRF-042" used as display name
    asset_type: str
    zone: str
    lat: float
    lng: float
    risk_score: float
    priority_score: float
    risk_level: str              # lowercase: "critical"|"high"|"medium"|"low"
    customers_served: int
    has_critical_facility: int
    last_inspected: Optional[str] = None
    install_year: Optional[int] = None
    voltage_kv: Optional[float] = None
    manufacturer: Optional[str] = None
    capacity_mva: Optional[float] = None
    shap_values: Optional[List[ShapValueOut]] = None

    model_config = {"from_attributes": True}


# ── Sensor ────────────────────────────────────────────────────────────────────

class SensorReadingOut(BaseModel):
    timestamp: str
    temperature_c: Optional[float] = None
    vibration_mm_s: Optional[float] = None
    oil_quality_index: Optional[float] = None
    partial_discharge_mv: Optional[float] = None
    load_percent: Optional[float] = None
    ambient_temp_c: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Maintenance ───────────────────────────────────────────────────────────────

class MaintenanceTaskOut(BaseModel):
    task_id: str
    asset_id: str
    scheduled_date: str
    action: str
    crew: str
    priority: str
    status: str

    model_config = {"from_attributes": True}


# ── Summary ───────────────────────────────────────────────────────────────────

class SummaryOut(BaseModel):
    total_assets: int
    critical_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    maintenance_today: int
    last_updated: str


# ── Weather ───────────────────────────────────────────────────────────────────

class WeatherAlertOut(BaseModel):
    id: int
    zone: str
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    model_config = {"from_attributes": True}
