# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [ ] **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads/)
- [ ] **Node.js 18+** (includes npm) — [nodejs.org](https://nodejs.org/)
- [ ] **Git**

No Docker, no cloud accounts, and no paid API keys are required to run the full demo.  
An OpenWeatherMap free API key is **optional** for live weather data (synthetic weather is the default).

---

## Environment Variables

### Data pipeline (`src/` root)

Copy `src/.env.example` to `src/.env`:

```bash
cp src/.env.example src/.env
```

| Variable | Description | Required |
|---|---|---|
| `OPENWEATHERMAP_API_KEY` | Free API key from [openweathermap.org/api](https://openweathermap.org/api). Only needed if you want live 5-day forecast data instead of synthetic weather. | No |

All other variables in `src/.env.example` (`WATSONX_API_KEY`, `DATABASE_URL`, etc.) are **not used** by the current implementation — they are template placeholders. Leave them as-is.

### Frontend (`src/frontend/`)

Copy `src/frontend/.env.example` to `src/frontend/.env`:

```bash
cp src/frontend/.env.example src/frontend/.env
```

| Variable | Description | Required |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API base URL. Default `/api` is correct for local dev (mock mode). | Yes (default value works) |

---

## Installation & Running

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-org/bob-ai-hackathon-telemetry-titans.git
cd bob-ai-hackathon-telemetry-titans
```

### Step 2 — Generate the dataset (Python)

```bash
cd src/data
pip install -r requirements.txt
python run_all.py
```

Expected output (takes ~4 seconds):

```
============================================================
  Telemetry Titans - Data Generation Pipeline
============================================================

[1/6] Generating grid topology...
  -> Saved src/data/processed/assets.csv
[2/6] Generating weather alerts...
  -> Saved src/data/processed/weather_alerts.csv
[3/6] Generating sensor readings...
  -> Saved src/data/processed/sensor_readings.csv
[4/6] Generating historical incidents...
  -> Saved src/data/processed/historical_incidents.csv
[5/6] Generating grid zone metadata...
  -> Saved src/data/processed/grid_zones.csv
[6/6] Merging into SQLite database...
============================================================
  Pipeline complete in 3.8s
  Output directory: src/data/processed
============================================================
```

This writes CSVs to `src/data/processed/` and the SQLite database to `src/data/output/grid_data.db`.

**Optional — verify data integrity:**

```bash
python verify_data.py
```

### Step 3 — Run the frontend dashboard

Open a new terminal:

```bash
cd src/frontend
cp .env.example .env        # uses default VITE_API_BASE_URL=/api
npm install
npm run dev
```

The dashboard will be available at: **`http://localhost:5173`**

The frontend runs in **mock-data mode** by default (no backend required). All pages — Dashboard, Map View, Asset Table, Asset Detail, Maintenance Plan, Calendar, Weather, Settings — are fully functional with the rich mock dataset in `src/frontend/src/mock/`.

---

## Optional — Live Weather Data

To replace synthetic weather alerts with real OpenWeatherMap 5-day forecasts:

1. Register for a free key at <https://openweathermap.org/api> (the free "Current Weather & Forecast" tier is sufficient)
2. Set `OPENWEATHERMAP_API_KEY=your_key_here` in `src/.env`
3. From `src/data/`:

```bash
python fetch_weather.py
```

This replaces `src/data/processed/weather_alerts.csv` with live forecast data, then re-run `python merge_to_db.py` to update the SQLite database.

---

## Running Tests / Validation

```bash
# From src/data/ — validates row counts, ID formats, cross-file consistency
python verify_data.py

# Frontend lint
cd src/frontend
npm run lint
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | Run `pip install -r requirements.txt` from `src/data/` |
| `python: command not found` | Use `python3` instead, or ensure Python 3.11 is on your PATH |
| `npm: command not found` | Install Node.js 18+ from [nodejs.org](https://nodejs.org/) |
| `npm install` fails with ERESOLVE | Run `npm install --legacy-peer-deps` |
| Blank map on the Map View page | Check browser console — Leaflet requires a valid tile URL. The default OpenStreetMap tiles need internet access. |
| `verify_data.py` reports missing processed files | Run `python run_all.py` first to generate the CSVs |
| Frontend shows "Failed to fetch" error | This is expected in mock mode — the API client falls back to mock data automatically. Check `src/frontend/src/store/useAppStore.ts` if you want to debug further. |
