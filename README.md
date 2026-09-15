# ⚡ GridHealth AI

> **Predictive grid-health monitoring and maintenance prioritisation for power utilities.**  
> IBM Bob AI Innovation Hackathon 2026 — Team Telemetry Titans

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Telemetry Titans |
| **Track** | AI |
| **Team Lead** | Vedant Patel (24DCS092) — 24dcs092@charusat.edu.in |
| **Members** | Yug Umrania (24DCS140) — 24dcs140@charusat.edu.in |
| | Parth Thakkar (24DCS135) — 24dcs135@charusat.edu.in |
| | Het Talpara (24DCS132) — 24dcs132@charusat.edu.in |

---

## 🎯 Problem Statement

Power transformer and substation failures cause blackouts costing utilities $1 M+/hour and affecting millions of people. Most utilities still use calendar-based maintenance, while sensors already measuring temperature, vibration, partial discharge, and oil quality show failure signatures weeks in advance. Weather events compound the risk — but sensor data and weather forecasts are never combined in time to act.

---

## 💡 Solution

GridHealth AI is a full-stack predictive monitoring platform that fuses transformer/substation sensor telemetry, live OpenWeatherMap weather forecasts, and three years of historical incident data into a real-time risk-ranked view of every grid asset. An XGBoost model scores failure probability per asset; a priority formula weighs that score against customers served, critical-facility proximity, and active weather alerts. A React dashboard surfaces risk on a live Leaflet map, explains predictions via SHAP, and auto-generates a crew-assigned maintenance plan.

---

## ✨ Key Features

- **XGBoost Failure Prediction:** Trained on aggregated 30-day sensor trends (temperature, vibration, oil quality, partial discharge) + incident history; scores 0–100 failure risk per asset.
- **Priority-Weighted Risk Ranking:** Composite score = 50% model risk + 25% customers served + 15% critical facility bonus + 10% active weather bonus.
- **SHAP Explainability:** Per-asset feature contribution breakdown so engineers know *why* an asset is flagged.
- **Live Weather Integration:** `GET /api/v1/weather/live?area=Maharashtra` fetches real OpenWeatherMap 5-day forecasts, classifies them into typed alert events, and overlays them on risk scores.
- **Interactive Grid Map:** Leaflet map with colour-coded risk markers across 5 geographic zones.
- **Auto-Generated Maintenance Plan:** Backend schedules CRITICAL assets for day 0, HIGH for days 1–2, MEDIUM for days 3–6, LOW for days 7–13 — with round-robin crew assignment.
- **Asset Detail + SHAP Charts:** Per-asset sensor trend charts (Recharts), SHAP bar chart, and full inspection metadata.
- **4 Themes:** Dark, Light, High Contrast Dark, High Contrast Light — fully consistent across all pages.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.11, TypeScript 5, JavaScript |
| **Backend** | FastAPI 0.111, Uvicorn, SQLAlchemy 2.0, Pydantic v2 |
| **ML / AI** | XGBoost 2.0, SHAP 0.45, scikit-learn 1.4, pandas, NumPy |
| **Frontend** | React 18, Vite, Tailwind CSS, React Router v7 |
| **Frontend Libraries** | Leaflet / react-leaflet, Recharts, TanStack Table v8, Zustand, Axios |
| **IBM Technologies** | IBM Bob (AI coding assistant used throughout development) |
| **Database** | SQLite (`grid_data.db`) — single shared DB for all layers |
| **Other** | OpenWeatherMap API, GitHub Actions, python-dotenv |

---

## 📁 Repository Structure

```
bob-ai-hackathon-telemetry-titans/
├── src/
│   ├── data/                  # Python synthetic data generation pipeline
│   │   ├── run_all.py         # Step 1 — generates all CSVs + SQLite DB (~4s)
│   │   ├── generate_*.py      # Individual generators (topology, sensors, weather, incidents, zones)
│   │   ├── fetch_weather.py   # Live OWM forecast → weather_alerts.csv
│   │   ├── merge_to_db.py     # Loads CSVs → grid_data.db
│   │   ├── verify_data.py     # Data integrity checker
│   │   ├── config.py          # Tuning knobs (seeds, thresholds, counts, paths)
│   │   └── requirements.txt
│   ├── backend/               # FastAPI + XGBoost + SHAP
│   │   ├── app/
│   │   │   ├── main.py            # FastAPI app, CORS, router registration
│   │   │   ├── config.py          # Settings (DB URL, OWM key, CORS)
│   │   │   ├── routers/           # assets, maintenance, summary, weather
│   │   │   ├── services/          # prediction.py (XGBoost+SHAP), maintenance_gen.py, live_weather.py
│   │   │   └── db/                # SQLAlchemy models, seed.py (Step 2)
│   │   └── requirements.txt
│   ├── frontend/              # React 18 + TypeScript dashboard
│   │   └── src/
│   │       ├── pages/         # Dashboard, MapView, AssetTable, AssetDetail, Maintenance, Calendar, Weather, Settings
│   │       ├── components/    # Charts (RiskGauge, SensorTrend, SHAP), Map, Tables, UI primitives
│   │       ├── store/         # Zustand app state — tries API, falls back to mock
│   │       ├── mock/          # Rich mock data for offline/demo use
│   │       └── types/         # Shared TypeScript domain types
│   └── ml/                    # Trained model artefacts (populated by seed.py)
│       └── models/
├── docs/
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/
├── presentation/
├── DATA_SCHEMA.md
└── submission.yaml
```

---

## ⚡ How to Run

Full instructions are in [`docs/setup-guide.md`](docs/setup-guide.md). Quick start (3 steps):

```bash
# Step 1 — Generate dataset (Python)
cd src/data
pip install -r requirements.txt
python run_all.py            # → src/data/output/grid_data.db (~4 s)

# Step 2 — Seed ML scores (Python, from src/backend/)
cd ../backend
pip install -r requirements.txt
python -m app.db.seed        # → trains XGBoost, writes risk_scores + maintenance_tasks

# Step 3a — Start backend
uvicorn app.main:app --reload --port 8000

# Step 3b — Start frontend (new terminal)
cd ../frontend
cp .env.example .env
npm install && npm run dev   # → http://localhost:5173
```

> The frontend automatically falls back to rich mock data if the backend is not running.

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |
| 📖 API Docs | `http://localhost:8000/docs` (when backend is running) |

---

## ⚠️ Known Limitations

- The ML model uses synthetic rule-based labels (no real SCADA outage ground truth) — the XGBoost model learns from the same failure physics rules used to generate the sensor data. In a production deployment these would be replaced by actual historical outage labels.
- The live weather endpoint (`/api/v1/weather/live`) requires a free OpenWeatherMap API key; without it, it returns an empty list (the DB-backed `/api/v1/weather` endpoint works without a key).
- Authentication/authorisation is not implemented — not production-ready.
- The frontend sensor trend charts on the Asset Detail page show mock data; wiring them to the real `GET /api/v1/assets/{id}/sensors` endpoint is the next step.
- Tested on Chrome and Firefox; mobile layout is functional but not fully optimised.

---

## 🏅 What We're Most Proud Of

The **complete, integrated pipeline**: synthetic sensor data with real transformer-failure physics → XGBoost model trained on it → SHAP-explained predictions → FastAPI endpoints → React dashboard — all sharing a single SQLite database, all runnable from scratch in under 5 minutes with three commands. The live weather overlay that pulls real OpenWeatherMap forecasts, classifies them into typed alert events, and automatically adjusts asset priority scores is the standout feature that makes the system genuinely useful beyond a demo.
