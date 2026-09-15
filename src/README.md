# Source Code

This directory contains all GridGuard AI source code, organized into two sub-projects:

```
src/
├── data/           ← Python data-generation pipeline
├── frontend/       ← React + TypeScript dashboard SPA
├── .env.example    ← Environment variable template (root-level, for Python scripts)
└── README.md       ← This file
```

---

## `src/data/` — Python Data Pipeline

Generates all synthetic datasets and loads them into a SQLite database.

```
src/data/
├── run_all.py              ← Master orchestrator — run this first
├── generate_topology.py    ← Produces assets.csv (105 transformers + substations)
├── generate_sensors.py     ← Produces sensor_readings.csv (75 600 hourly rows)
├── generate_weather.py     ← Produces weather_alerts.csv (synthetic events)
├── fetch_weather.py        ← Optional: live OpenWeatherMap 5-day forecasts
├── generate_incidents.py   ← Produces historical_incidents.csv (300 records)
├── generate_grid_zones.py  ← Produces grid_zones.csv (derived from assets)
├── merge_to_db.py          ← Loads all CSVs into output/grid_data.db (SQLite)
├── verify_data.py          ← Validates row counts, ID formats, cross-file integrity
├── config.py               ← All tuning knobs: seeds, thresholds, zone config, paths
├── schema.sql              ← SQLite DDL for all 5 tables
├── requirements.txt        ← Python dependencies (pandas, numpy, requests, python-dotenv)
├── processed/              ← Generated CSV output (created by run_all.py)
└── output/                 ← SQLite database output (created by run_all.py)
```

**Quick start:**
```bash
cd src/data
pip install -r requirements.txt
python run_all.py
```

See [`docs/setup-guide.md`](../../docs/setup-guide.md) for full instructions.

---

## `src/frontend/` — React Dashboard

A TypeScript/React 18 single-page application built with Vite.

```
src/frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── .env.example            ← Frontend env vars (VITE_API_BASE_URL)
└── src/
    ├── App.tsx             ← Root component — routing setup
    ├── main.tsx            ← Entry point
    ├── index.css           ← Global styles
    ├── pages/              ← Full-page views
    │   ├── Dashboard.tsx       ← KPI cards, top-risk assets, mini map
    │   ├── MapView.tsx         ← Full-screen Leaflet map with risk markers
    │   ├── AssetTable.tsx      ← Sortable/filterable asset list (TanStack Table)
    │   ├── AssetDetail.tsx     ← Per-asset sensor trends + SHAP explanation
    │   ├── MaintenancePlan.tsx ← Prioritised work-order list
    │   ├── CalendarPage.tsx    ← Monthly maintenance calendar
    │   ├── WeatherPage.tsx     ← Active weather alerts by zone
    │   └── SettingsPage.tsx    ← Theme and display preferences
    ├── components/
    │   ├── charts/
    │   │   ├── RiskGauge.tsx       ← Circular risk score gauge
    │   │   ├── SensorTrendChart.tsx← Line chart for sensor history
    │   │   └── ShapBarChart.tsx    ← SHAP feature-importance bar chart
    │   ├── map/
    │   │   ├── GridMap.tsx         ← Leaflet map container
    │   │   └── RiskMarker.tsx      ← Colour-coded asset marker + popup
    │   ├── tables/
    │   │   └── AssetRiskTable.tsx  ← TanStack Table wrapper
    │   └── ui/
    │       ├── Navbar.tsx          ← Top navigation bar
    │       ├── Sidebar.tsx         ← Desktop + mobile sidebar
    │       ├── StatCard.tsx        ← KPI summary card
    │       ├── StatusBadge.tsx     ← Risk/status pill badges
    │       └── LoadingSpinner.tsx  ← Loading state indicator
    ├── store/
    │   └── useAppStore.ts      ← Zustand store (assets, tasks, filters, loadData)
    ├── api/
    │   └── client.ts           ← Axios instance pointing at VITE_API_BASE_URL
    ├── mock/
    │   ├── mockData.ts         ← Rich mock assets + maintenance tasks
    │   ├── weatherMockData.ts  ← Mock weather alerts
    │   └── calendarMockData.ts ← Mock calendar events
    ├── types/
    │   └── index.ts            ← Domain types: Asset, SensorReading, MaintenanceTask, etc.
    ├── theme/
    │   └── themeUtils.ts       ← Dark/light theme helpers
    └── settings/
        └── useSettingsStore.ts ← Persisted settings (theme, units)
```

**Quick start:**
```bash
cd src/frontend
cp .env.example .env
npm install
npm run dev           # → http://localhost:5173
```

The frontend runs on mock data by default — no backend is needed. See [`docs/setup-guide.md`](../../docs/setup-guide.md) for details.

---

## What NOT to Commit

The following are already in `.gitignore` — do not commit them:

- `.env` files with real credentials
- `node_modules/`
- `__pycache__/`, `.venv/`
- `src/data/processed/` and `src/data/output/` (generated artefacts — regenerate with `run_all.py`)
- Frontend build artefacts (`dist/`)
