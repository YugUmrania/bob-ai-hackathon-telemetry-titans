from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, UniqueConstraint
)
from ..db.database import Base


class Asset(Base):
    __tablename__ = "assets"

    asset_id             = Column(String, primary_key=True, index=True)
    asset_type           = Column(String, nullable=False)   # transformer | substation
    zone                 = Column(String, nullable=False)
    lat                  = Column(Float,  nullable=False)
    lng                  = Column(Float,  nullable=False)
    customers_served     = Column(Integer, default=0)
    has_critical_facility = Column(Integer, default=0)     # 1 = yes
    last_inspected       = Column(String)                  # ISO date
    install_year         = Column(Integer)
    voltage_kv           = Column(Float)
    manufacturer         = Column(String)
    capacity_mva         = Column(Float)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    reading_id              = Column("reading_id", Integer, primary_key=True, autoincrement=True)
    asset_id                = Column(String, ForeignKey("assets.asset_id"), nullable=False, index=True)
    timestamp               = Column(String, nullable=False)
    temperature_c           = Column(Float)
    vibration_mm_s          = Column(Float)
    oil_quality_index       = Column(Float)
    partial_discharge_mv    = Column(Float)
    load_percent            = Column(Float)
    ambient_temp_c          = Column(Float)

    __table_args__ = (UniqueConstraint("asset_id", "timestamp"),)


class RiskScore(Base):
    __tablename__ = "risk_scores"

    asset_id        = Column(String, ForeignKey("assets.asset_id"), primary_key=True)
    risk_score      = Column(Float, nullable=False)
    priority_score  = Column(Float, nullable=False)
    risk_level      = Column(String, nullable=False)   # CRITICAL | HIGH | MEDIUM | LOW
    computed_at     = Column(String, nullable=False)


class ShapValue(Base):
    __tablename__ = "shap_values"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    asset_id     = Column(String, ForeignKey("assets.asset_id"), nullable=False, index=True)
    feature      = Column(String, nullable=False)
    contribution = Column(Float, nullable=False)


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    task_id        = Column(String, primary_key=True)
    asset_id       = Column(String, ForeignKey("assets.asset_id"), nullable=False, index=True)
    scheduled_date = Column(String, nullable=False)
    action         = Column(String, nullable=False)
    crew           = Column(String, nullable=False)
    priority       = Column(String, nullable=False)
    status         = Column(String, nullable=False, default="scheduled")


class WeatherAlert(Base):
    __tablename__ = "weather_alerts"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    zone             = Column(String, nullable=False, index=True)
    alert_type       = Column(String)   # storm | heatwave | high_wind | ice_storm | flood
    severity         = Column(String)
    start_time       = Column(String)
    end_time         = Column(String)
    max_wind_kmh     = Column(Float)
    max_temp_c       = Column(Float)
    precipitation_mm = Column(Float)


class GridZone(Base):
    __tablename__ = "grid_zones"

    zone               = Column(String, primary_key=True)
    region_label       = Column(String)
    center_lat         = Column(Float)
    center_lng         = Column(Float)
    total_customers    = Column(Integer)
    critical_facilities = Column(Integer)
    area_km2           = Column(Float)


class HistoricalIncident(Base):
    __tablename__ = "historical_incidents"

    incident_id          = Column(String, primary_key=True)
    asset_id             = Column(String, ForeignKey("assets.asset_id"), nullable=False, index=True)
    incident_date        = Column(String, nullable=False)
    incident_type        = Column(String)
    severity             = Column(String)
    outage_duration_hrs  = Column(Float)
    customers_affected   = Column(Integer)
    repair_cost_usd      = Column(Float)
    weather_related      = Column(Integer, default=0)
    root_cause           = Column(Text)
