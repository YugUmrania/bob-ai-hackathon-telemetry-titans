# Solution Overview

## What We Built

GridHealth AI is a full-stack predictive grid-health monitoring platform. It ingests physically realistic synthetic sensor telemetry from transformers and substations, processes it through an XGBoost ML model, exposes the predictions via a FastAPI REST API, and visualises everything in a React dashboard. Maintenance planners see which assets are most likely to fail, why (via SHAP), and get an auto-generated, crew-assigned work order list — all before an outage happens.

## How It Works

1. **Data pipeline** (`src/data/run_all.py`): Generates the entire dataset in ~4 seconds — 105 grid assets across 5 zones, 75,600 hourly sensor readings over 30 days, 300 historical incidents, ~150 weather alerts, and zone metadata. Outputs are 5 CSVs merged into `src/data/output/grid_data.db` (SQLite).

2. **Sensor failure physics**: Each asset is assigned a hidden health tier — *healthy* (60%), *degrading* (25%), or *near-failure* (15%). Near-failure assets follow real transformer-failure physics: oil temperature rises ~0.5 °C/day, partial discharge spikes after day 15, vibration spikes in the final 48–72 hours. This gives the model genuine signal to learn from.

3. **ML seeding** (`src/backend/app/db/seed.py`): Reads the data team's SQLite DB, engineers 11 features per asset (sensor aggregates + asset age + incident count), trains an XGBoost regressor on synthetic labels derived from the same failure physics, computes SHAP values for each asset, and writes `risk_scores`, `shap_values`, and `maintenance_tasks` tables back into the same DB.

4. **Priority scoring**: `priority_score = risk_score×0.50 + customers_norm×0.25 + has_critical_facility×15 + weather_bonus×10`. An active HIGH/CRITICAL weather alert in the asset's zone adds 10 points to its priority.

5. **FastAPI backend** (`src/backend/app/main.py`): Serves four route groups:
   - `GET /api/v1/assets` — all assets with risk scores, filterable by risk level / zone
   - `GET /api/v1/assets/{id}` — single asset with SHAP explanations
   - `GET /api/v1/assets/{id}/sensors` — 30-day sensor time-series
   - `GET /api/v1/summary` — grid-wide KPI counts for dashboard header cards
   - `GET /api/v1/maintenance` — sorted work orders
   - `GET /api/v1/weather` — historical/synthetic alerts from DB
   - `GET /api/v1/weather/live?area=Maharashtra` — real-time OWM forecasts

6. **Live weather** (`src/backend/app/services/live_weather.py`): Given any Indian state name, spreads 5 zone centers around the state capital, fetches the free OWM 5-day/3-hour forecast for each, classifies forecast slots by wind/temperature/precipitation thresholds, and groups consecutive severe slots into typed alert events (storm, heatwave, high_wind, ice_storm, flood) — same schema as the data pipeline's synthetic alerts.

7. **React dashboard** (`src/frontend`): Eight pages served by a React 18 SPA:
   - **Dashboard** — KPI cards, top-5 at-risk assets, upcoming maintenance, mini grid map
   - **Map View** — full-screen Leaflet map with colour-coded risk markers
   - **Asset Table** — sortable/filterable table (TanStack Table v8)
   - **Asset Detail** — sensor trend charts, SHAP bar chart, inspection metadata
   - **Maintenance Plan** — priority-sorted work-order list with crew assignment
   - **Calendar** — monthly/weekly/list view of all maintenance events
   - **Weather** — active and historical alerts per zone
   - **Settings** — theme, text size, density, notification preferences

8. **Graceful fallback**: The Zustand store tries `GET /api/v1/assets` on load; if the backend is not running it silently falls back to the rich mock dataset in `src/frontend/src/mock/`, so all pages remain fully functional for demo purposes.

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the full Mermaid diagram.

```
[OpenWeatherMap API]    [Sensor / Incident data (synthetic)]
        │                           │
        ▼                           ▼
 fetch_weather.py          generate_*.py / run_all.py
        │                           │
        └─────────────┬─────────────┘
                      ▼
              merge_to_db.py → grid_data.db (SQLite)
                      │
                      ▼
         app/db/seed.py (XGBoost + SHAP + maintenance_gen)
                      │ writes risk_scores, shap_values, maintenance_tasks
                      ▼
         FastAPI app  (uvicorn app.main:app)
                      │  REST /api/v1/*
                      ▼
         React 18 SPA (Vite, http://localhost:5173)
              │
   ┌──────────┼──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼          ▼
Dashboard  MapView  AssetTable  AssetDetail  Maintenance
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Single SQLite DB shared by all three layers | Eliminates networking complexity for the hackathon; the data pipeline writes 5 tables, the backend adds 3 ML tables to the same file — no separate DB server needed |
| XGBoost over deep learning | Interpretable, fast to train on tabular sensor data, directly supports SHAP TreeExplainer; matches how utilities actually audit AI decisions |
| Synthetic labels derived from failure physics | No real SCADA outage labels available; using the same physics rules as the data generator means the model's predictions are coherent with the data's ground truth tiers |
| SHAP explainability | A raw risk score is not actionable; the SHAP bar chart on the Asset Detail page tells the engineer exactly which sensor is the primary driver |
| Frontend mock fallback | Decouples UI development from backend; judges can evaluate the dashboard without running Python at all |
| Separate `seed.py` from FastAPI startup | The ML training step is slow (~10s) and only needs to run once; keeping it out of the request path means the API starts instantly |
| Priority formula weights | 50% model risk ensures the ML signal dominates; 25% customers normalised prevents large assets from always topping the list; the weather bonus makes active alerts immediately visible in the ranking |

## IBM Technologies Used

- **IBM Bob:** Used as the primary AI coding assistant throughout the project — architecture decisions, code generation for TypeScript components and Python pipeline scripts, debugging, CSS theme fixes, and documentation. IBM Bob's ability to hold the full codebase context across multiple files simultaneously was critical for keeping the data pipeline schema, SQLAlchemy models, Pydantic schemas, and TypeScript types in sync across a four-person team working in parallel.
