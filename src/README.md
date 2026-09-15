# Source Code

This directory contains all GridHealth AI source code, organised into three sub-projects that share a single SQLite database.

```
src/
├── data/       ← Python data-generation pipeline (run first)
├── backend/    ← FastAPI + XGBoost + SHAP REST API (run second)
├── frontend/   ← React 18 + TypeScript dashboard (run third)
├── ml/         ← Trained model artefacts (populated automatically by seed.py)
│   └── models/
└── .env.example  ← Root-level env template (for data pipeline scripts)
```

> **Run order:** `src/data/run_all.py` → `src/backend/app/db/seed.py` → `uvicorn` + `npm run dev`  
> See [`docs/setup-guide.md`](../docs/setup-guide.md) for full step-by-step instructions.

---

## `src/data/` — Synthetic Data Pipeline

Generates all five datasets and loads them into the shared SQLite database.

```
src/data/
├── run_all.py              ← Master orchestrator — run this first
├── generate_topology.py    ← assets.csv: 105 transformers + substations, 5 Delhi-NCR zones
├── generate_sensors.py     ← sensor_readings.csv: 75,600 hourly rows, 3 health tiers
├── generate_weather.py     ← weather_alerts.csv: synthetic events 2023–2026
├── fetch_weather.py        ← Optional: live OWM 5-day forecast → weather_alerts.csv
├── generate_incidents.py   ← historical_incidents.csv: 300 incident records
├── generate_grid_zones.py  ← grid_zones.csv: zone metadata derived from assets
├── merge_to_db.py          ← Loads all CSVs → output/grid_data.db (SQLite)
├── verify_data.py          ← Validates row counts, ID formats, cross-file integrity
├── config.py               ← All tuning knobs: seeds, thresholds, zone config, paths
├── schema.sql              ← SQLite DDL for all 5 data tables
├── requirements.txt        ← pandas, numpy, requests, python-dotenv
├── processed/              ← Generated CSV output (git-ignored)
├── output/                 ← SQLite DB output (git-ignored)
└── raw/                    ← Raw source data placeholder
```

**Quick start:**
```bash
cd src/data
pip install -r requirements.txt
python run_all.py
```

### Sensor Health Tiers

| Tier | % of assets | Behaviour |
|---|---|---|
| healthy | 60% | All sensors in normal range with small noise |
| degrading | 25% | 1–2 sensors drift toward warning range over 30 days |
| near-failure | 15% | 2+ sensors in critical range; temperature rises 0.5 °C/day; vibration spikes in final 48–72 hours |

---

## `src/backend/` — FastAPI REST API

Reads the data team's SQLite DB, runs ML scoring, and serves a REST API.

```
src/backend/
├── app/
│   ├── main.py             ← FastAPI app: CORS, router registration, ML table init
│   ├── config.py           ← Pydantic settings: DATABASE_URL, CORS_ORIGIN, OWM key
│   ├── routers/
│   │   ├── assets.py       ← GET /api/v1/assets, /{id}, /{id}/sensors
│   │   ├── summary.py      ← GET /api/v1/summary
│   │   ├── maintenance.py  ← GET /api/v1/maintenance
│   │   └── weather.py      ← GET /api/v1/weather, /weather/live, /weather/areas
│   ├── services/
│   │   ├── prediction.py   ← XGBoost feature engineering, train/load, SHAP, priority scoring
│   │   ├── maintenance_gen.py ← Risk-tier scheduling + round-robin crew assignment
│   │   └── live_weather.py ← OWM 5-day forecast fetch, classify, group into alert events
│   ├── db/
│   │   ├── database.py     ← SQLAlchemy engine + SessionLocal
│   │   ├── models.py       ← ORM models: Asset, SensorReading, RiskScore, ShapValue,
│   │   │                      MaintenanceTask, WeatherAlert, GridZone, HistoricalIncident
│   │   └── seed.py         ← One-shot ML seeder: verifies data tables → trains XGBoost
│   │                          → writes risk_scores + shap_values + maintenance_tasks
│   └── models/
│       └── schemas.py      ← Pydantic response schemas for all endpoints
├── tests/
│   ├── conftest.py         ← pytest fixtures (TestClient, in-memory SQLite)
│   └── test_endpoints.py   ← API endpoint integration tests
├── .env.example            ← DATABASE_URL, CORS_ORIGIN, PORT, OPENWEATHERMAP_API_KEY
├── drop_ml_tables.py       ← Utility: drop risk_scores + shap_values + maintenance_tasks
└── requirements.txt        ← fastapi, uvicorn, sqlalchemy, xgboost, shap, pandas, ...
```

**Quick start:**
```bash
cd src/backend
pip install -r requirements.txt
python -m app.db.seed          # trains model, seeds risk scores (~10–20 s first run)
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

### ML Feature Columns

The XGBoost model is trained on 11 features aggregated from the last 30 days of sensor readings:

```
temperature_c_mean, temperature_c_max,
vibration_mm_s_mean, vibration_mm_s_max,
oil_quality_index_mean, oil_quality_index_min,
partial_discharge_mv_mean, partial_discharge_mv_max,
load_percent_mean,
asset_age_years,
incident_count_past_year
```

### Priority Score Formula

```
priority = risk_score × 0.50
         + (customers_served / max_customers × 100) × 0.25
         + has_critical_facility × 15
         + weather_bonus × 10     ← +1 if active HIGH/CRITICAL alert in zone
```

---

## `src/frontend/` — React Dashboard

React 18 + TypeScript SPA built with Vite. Connects to the FastAPI backend; falls back to mock data if the backend is unavailable.

```
src/frontend/
├── index.html
├── package.json            ← React 18, Leaflet, Recharts, TanStack Table, Zustand, Axios, ...
├── vite.config.ts          ← Dev server proxy /api → localhost:8000
├── tailwind.config.js
├── .env.example            ← VITE_API_BASE_URL=http://localhost:8000
└── src/
    ├── App.tsx             ← Root component: BrowserRouter + all route definitions
    ├── main.tsx            ← Entry point: initTheme() before React mounts
    ├── index.css           ← CSS design tokens for 4 themes + component utility classes
    ├── pages/
    │   ├── Dashboard.tsx       ← KPI cards, top-5 at-risk, upcoming maintenance, mini map
    │   ├── MapView.tsx         ← Full-screen Leaflet map with risk markers
    │   ├── AssetTable.tsx      ← Sortable/filterable asset list
    │   ├── AssetDetail.tsx     ← Sensor trends, SHAP chart, inspection history
    │   ├── MaintenancePlan.tsx ← Priority-sorted work orders
    │   ├── CalendarPage.tsx    ← Month/week/list maintenance calendar
    │   ├── WeatherPage.tsx     ← Alerts by zone + live OWM fetch
    │   └── SettingsPage.tsx    ← Theme, text size, density, notification prefs
    ├── components/
    │   ├── charts/
    │   │   ├── RiskGauge.tsx        ← Circular 0–100 risk score gauge
    │   │   ├── SensorTrendChart.tsx ← 30-day sensor line chart
    │   │   └── ShapBarChart.tsx     ← SHAP feature-importance bar chart
    │   ├── map/
    │   │   ├── GridMap.tsx          ← Leaflet map container
    │   │   └── RiskMarker.tsx       ← Colour-coded marker + popup
    │   ├── tables/
    │   │   └── AssetRiskTable.tsx   ← TanStack Table wrapper
    │   └── ui/
    │       ├── Navbar.tsx, Sidebar.tsx
    │       ├── StatCard.tsx, StatusBadge.tsx, LoadingSpinner.tsx
    ├── store/
    │   └── useAppStore.ts       ← Zustand: loads from API or mock; filters; theme
    ├── api/
    │   └── client.ts            ← Axios instance (unused — store uses native fetch)
    ├── mock/
    │   ├── mockData.ts          ← Full mock asset + maintenance task dataset
    │   ├── weatherMockData.ts   ← Mock weather alerts
    │   └── calendarMockData.ts  ← Mock calendar events
    ├── types/index.ts           ← Domain types: Asset, SensorReading, MaintenanceTask, ...
    ├── theme/themeUtils.ts      ← Theme ID enum, applyTheme(), initTheme()
    └── settings/useSettingsStore.ts ← Zustand settings store (persisted to localStorage)
```

**Quick start:**
```bash
cd src/frontend
cp .env.example .env
npm install
npm run dev    # → http://localhost:5173
```

---

## `src/ml/` — Model Artefacts

```
src/ml/
└── models/   ← Populated by seed.py: gridhealth_model.pkl saved here
              ← git-ignored (regenerated on each seed run)
```

---

## What NOT to Commit

Already covered by `.gitignore`:

- `.env` files with real credentials
- `node_modules/`, `__pycache__/`, `.venv/`
- `src/data/processed/`, `src/data/output/` — regenerate with `run_all.py`
- `src/ml/models/*.pkl` — regenerate with `seed.py`
- Frontend build artefacts (`dist/`)
