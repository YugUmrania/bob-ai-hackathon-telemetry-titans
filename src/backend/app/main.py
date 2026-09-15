from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Ensure the data/output/ directory exists before the engine tries to open the DB.
# This prevents a crash when the data team hasn't run run_all.py yet.
_db_path_str = str(settings.database_url).replace("sqlite:///", "")
Path(_db_path_str).parent.mkdir(parents=True, exist_ok=True)

from app.db.database import engine
from app.db.models import RiskScore, ShapValue, MaintenanceTask
from app.routers import assets, maintenance, summary, weather

# Only create the 3 ML-owned tables on startup.
# The 5 data tables are created by src/data/run_all.py — we never touch them.
from sqlalchemy import inspect as _inspect
_existing_tables = set(_inspect(engine).get_table_names())
for _tbl in [RiskScore.__table__, ShapValue.__table__, MaintenanceTask.__table__]:
    if _tbl.name not in _existing_tables:
        _tbl.create(engine)

app = FastAPI(
    title="GridHealth AI",
    description=(
        "Power Outage Prediction & Grid Equipment Failure Advisor.\n\n"
        "Combines asset health sensor data, weather forecasts, and historical "
        "incident records to predict at-risk transformers and substations, "
        "rank them by grid impact, and generate a prioritised maintenance plan."
    ),
    version="1.0.0",
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(summary.router)
app.include_router(assets.router)
app.include_router(maintenance.router)
app.include_router(weather.router)


@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "project": "GridHealth AI",
        "docs": "/docs",
        "endpoints": [
            "GET /api/v1/summary",
            "GET /api/v1/assets",
            "GET /api/v1/assets/{asset_id}",
            "GET /api/v1/assets/{asset_id}/sensors",
            "GET /api/v1/maintenance",
            "GET /api/v1/weather",
            "GET /api/v1/weather?active_only=true",
        ],
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
