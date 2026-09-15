# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js | 18+ (includes npm) | [nodejs.org](https://nodejs.org/) |
| Git | Any | For cloning |

No Docker, no cloud account, and no paid API keys are required to run the full demo.  
An OpenWeatherMap **free** API key is optional (enables the live weather endpoint).

---

## Clone the Repository

```bash
git clone https://github.com/YugUmrania/bob-ai-hackathon-telemetry-titans.git
cd bob-ai-hackathon-telemetry-titans
```

---

## Step 1 — Generate the Dataset (Python)

```bash
cd src/data
pip install -r requirements.txt
python run_all.py
```

Expected output (~4 seconds):

```
============================================================
  Telemetry Titans - Data Generation Pipeline
============================================================
[1/6] Generating grid topology...
[2/6] Generating weather alerts...
[3/6] Generating sensor readings...
[4/6] Generating historical incidents...
[5/6] Generating grid zone metadata...
[6/6] Merging into SQLite database...
============================================================
  Pipeline complete in 3.8s
============================================================
```

**Outputs:**
- `src/data/processed/` — 5 CSV files
- `src/data/output/grid_data.db` — SQLite database (all 5 data tables)

**Optional — verify data integrity:**
```bash
python verify_data.py
```

---

## Step 2 — Seed ML Scores (Python)

This step trains XGBoost on the sensor data, computes SHAP values, and generates the maintenance plan. Run from `src/backend/`:

```bash
cd ../backend
pip install -r requirements.txt
python -m app.db.seed
```

Expected output (~10–20 seconds on first run; faster on subsequent runs if model is cached):

```
INFO  DB: sqlite:///../data/output/grid_data.db
INFO  Data check: 105 assets, 75600 sensor readings
INFO  Created table: risk_scores
INFO  Created table: shap_values
INFO  Created table: maintenance_tasks
INFO  Training new XGBoost model…
INFO  Model saved to …/data/output/gridhealth_model.pkl
INFO  Scored 105 assets
INFO  Generated 105 maintenance tasks
INFO  ✅  Seed complete.
```

This writes 3 new tables (`risk_scores`, `shap_values`, `maintenance_tasks`) into the existing `grid_data.db`.

---

## Step 3 — Start the Backend

From `src/backend/`:

```bash
# Copy env file and optionally add your OWM key
cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

The API will be available at: **`http://localhost:8000`**  
Interactive API docs: **`http://localhost:8000/docs`**

### Environment Variables (`src/backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///../data/output/grid_data.db` | Path to the SQLite DB created in Step 1 |
| `CORS_ORIGIN` | `http://localhost:5173` | Frontend origin for CORS |
| `PORT` | `8000` | Uvicorn port |
| `OPENWEATHERMAP_API_KEY` | *(empty)* | Free OWM key — only needed for `GET /api/v1/weather/live`. Leave blank to skip. |

---

## Step 4 — Start the Frontend

Open a **new terminal**:

```bash
cd src/frontend
cp .env.example .env      # sets VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

The dashboard will be available at: **`http://localhost:5173`**

### Environment Variables (`src/frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL. Change this if you run the backend on a different port. |

> **Note:** If the backend is not running, the frontend automatically falls back to rich mock data. All 8 pages are fully functional in mock mode — useful for a quick demo without running Python.

---

## Optional — Live Weather Data

1. Register for a free API key at <https://openweathermap.org/api> (the free "Current Weather & Forecast" tier is sufficient).
2. Set `OPENWEATHERMAP_API_KEY=your_key_here` in `src/backend/.env`.
3. In the frontend, navigate to the **Weather** page and select an Indian state to load real 5-day forecasts.

The live weather endpoint also reads the key from `src/data/.env` as a fallback — so if you already set it there for the data pipeline, the backend will pick it up automatically.

---

## Verifying Everything Works

With both backend and frontend running:

1. Open `http://localhost:5173` — the Dashboard should load with real asset data (not mock).
2. Open `http://localhost:8000/docs` — the Swagger UI should show all 8 endpoints.
3. Check `GET /api/v1/summary` returns `total_assets: 105`.
4. Check `GET /api/v1/assets?limit=5` returns 5 assets with `risk_score` values.

---

## Running Tests

```bash
# Backend tests (from src/backend/)
cd src/backend
pip install pytest httpx
pytest tests/ -v

# Frontend lint (from src/frontend/)
cd src/frontend
npm run lint

# Data integrity check (from src/data/)
cd src/data
python verify_data.py
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | Run `pip install -r requirements.txt` from `src/data/` |
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install -r requirements.txt` from `src/backend/` |
| `python: command not found` | Use `python3` on macOS/Linux, or ensure Python 3.11 is on PATH |
| `npm install` fails with `ERESOLVE` | Run `npm install --legacy-peer-deps` |
| `seed.py` fails: "Data tables missing" | Run `python run_all.py` from `src/data/` first |
| `seed.py` fails: "Assets table is empty" | The DB exists but is empty — re-run `python run_all.py` |
| Backend starts but frontend shows mock data | Confirm `VITE_API_BASE_URL=http://localhost:8000` in `src/frontend/.env` and that the backend is running |
| Blank map on Map View page | Leaflet tile loading requires internet access (OpenStreetMap CDN) |
| Live weather returns empty list | `OPENWEATHERMAP_API_KEY` is not set in `src/backend/.env` |
| `uvicorn: command not found` | Run `pip install uvicorn` or use `python -m uvicorn app.main:app --reload --port 8000` |
