# Solution Overview

## What We Built

GridGuard AI is a predictive grid-health monitoring dashboard for power utilities. It ingests synthetic (but physically realistic) sensor telemetry from transformers and substations, correlates it with weather forecasts and three years of historical incident data, and produces a risk-ranked view of every grid asset. Maintenance planners see at a glance which assets are most likely to fail, why, and what to do about it — all before an outage happens.

## How It Works

1. **Data generation pipeline (Python):** `run_all.py` orchestrates five generator scripts that produce a complete dataset — grid topology (`assets.csv`), hourly sensor readings for the last 30 days (`sensor_readings.csv`), weather alert events (`weather_alerts.csv`), historical incidents (`historical_incidents.csv`), and zone metadata (`grid_zones.csv`). All five CSVs are merged into a single SQLite database (`grid_data.db`).

2. **Sensor failure physics:** Each asset is assigned one of three hidden health tiers — *healthy* (60%), *degrading* (25%), or *near-failure* (15%). Near-failure assets follow real transformer-failure progression: oil temperature rises ~0.5 °C/day, partial discharge starts spiking after day 15, and vibration spikes in the final 48–72 hours before simulated failure. This gives the ML model ground truth to learn from.

3. **Risk scoring (XGBoost + SHAP):** A gradient-boosted classifier trained on sensor trends, asset age, load percentage, and weather exposure produces a per-asset failure probability for the next 7 days and 30 days. A composite risk score (0–100) is derived by weighting that probability against criticality factors — customers served, presence of critical facilities, and active weather alerts.

4. **React dashboard:** A TypeScript/React 18 single-page application serves the risk data across eight views:
   - **Dashboard** — KPI stat cards (critical/high/medium/low counts), top-5 at-risk assets, upcoming maintenance tasks, and a mini grid map.
   - **Map View** — Full-screen Leaflet map with colour-coded risk markers; click any marker to open the asset detail panel.
   - **Asset Table** — Sortable, filterable table of all assets (TanStack Table) with risk badges and status indicators.
   - **Asset Detail** — Sensor trend charts (Recharts), SHAP bar chart explaining which factors drive the risk score, and inspection history.
   - **Maintenance Plan** — Sorted work-order list with priority tier, estimated cost, assigned crew, and scheduled date.
   - **Calendar** — Monthly view of all maintenance events colour-coded by status.
   - **Weather Page** — Active and forecast weather alerts per zone with severity indicators.
   - **Settings** — Theme and display preferences (Zustand persisted state).

5. **Weather integration:** `fetch_weather.py` can optionally call the OpenWeatherMap free 5-day forecast API, classify forecast slots by wind speed, temperature, and precipitation thresholds, and group consecutive severe slots into alert events that feed directly into the same risk-scoring pipeline.

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the detailed component diagram.

```
[OpenWeatherMap API]          [SCADA / Sensors (simulated)]
        │                                  │
        ▼                                  ▼
 fetch_weather.py              generate_sensors.py / generate_topology.py
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
               merge_to_db.py  →  grid_data.db (SQLite)
                       │
                       ▼
             FastAPI backend (planned)
                       │  REST /api
                       ▼
             React 18 SPA (Vite)
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    GridMap        AssetTable    MaintenancePlan
  (Leaflet)      (TanStack)      (risk-sorted)
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Synthetic data with real failure physics | Allows a fully runnable demo without access to proprietary SCADA feeds; the physics match real transformer failure literature so the demo is scientifically credible |
| SQLite instead of PostgreSQL | Zero-setup for judges; the schema is identical to what a production PostgreSQL backend would use — switching databases requires only a connection string change |
| Frontend runs on mock data when backend is absent | Decouples UI development from backend readiness; the Zustand store's `loadData()` call can be pointed at the real API with a one-line change in `client.ts` |
| SHAP explainability | Risk scores without explanations are not actionable; SHAP factors tell the maintenance planner *why* an asset is high-risk (e.g., "partial discharge is the dominant driver") so they can order the right parts |
| XGBoost over deep learning | Interpretable, fast to train on tabular sensor data, and well-suited to small datasets (100 assets × 30 days); aligns with how utilities actually want to audit AI decisions |
| Zustand for state management | Lightweight — no boilerplate compared to Redux; the entire app state (assets, maintenance tasks, filters) fits in a single store file |

## IBM Technologies Used

- **IBM Bob:** Used as the primary AI coding assistant throughout the project — for architecture design, code generation (TypeScript components, Python pipeline scripts), debugging, and documentation. IBM Bob's ability to understand the full codebase context at once was critical for keeping the data pipeline schema, TypeScript types, and mock data in sync across a multi-person team.
