# ⚡ GridGuard AI

> **Predictive grid-health monitoring and maintenance prioritisation for power utilities.**  
> IBM Bob AI Innovation Hackathon 2026 — Team Telemetry Titans

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Telemetry Titans |
| **Track** | AI |
| **Team Lead** | Vedant Patel — 24dcs092@charusat.edu.in |
| **Members** | Het Talpara (24dcs132@charusat.edu.in), Parth Thakkar (24dcs135@charusat.edu.in), Yug Umrania (24dcs140@charusat.edu.in) |

---

## 🎯 Problem Statement

Power transformer and substation failures cause blackouts costing utilities $1 M+/hour and affecting millions of people. Most utilities still use calendar-based maintenance, while sensors already measuring temperature, vibration, partial discharge, and oil quality show failure signatures weeks in advance. Weather events compound the risk — but sensor data and weather forecasts are never combined in time to act.

---

## 💡 Solution

GridGuard AI combines transformer/substation sensor health data, weather forecasts, and historical incident records into risk-ranked predictions. It surfaces outage-prone assets on a live interactive map, ranks equipment by grid-impact severity, and generates a prioritised maintenance and crew pre-positioning plan — all in a single dashboard.

---

## ✨ Key Features

- **Failure Prediction Model (XGBoost):** Scores per-asset failure probability from real sensor trends (temperature, vibration, oil quality, partial discharge).
- **Risk-Ranking Formula:** Weighs sensor alarms, weather exposure, asset age, and number of customers served into a 0–100 risk score.
- **Interactive Grid Map:** Leaflet-powered map with colour-coded risk markers per asset and live weather-overlay context.
- **Prioritised Maintenance Planner:** Generates a sorted work order list with estimated cost, crew assignment, and urgency tier.
- **Asset Detail View:** Per-asset sensor trend charts (Recharts), SHAP feature-importance bar chart, and full inspection history.
- **Weather Threat Integration:** Live OpenWeatherMap 5-day forecasts classified into alert events (storm, heatwave, high wind, ice storm, flood) and overlaid on asset risk scores.
- **Maintenance Calendar:** Monthly calendar view of all scheduled, in-progress, and completed maintenance events.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.11, TypeScript 5, JavaScript |
| **Frameworks** | React 18, Vite, Tailwind CSS, FastAPI (backend — planned) |
| **ML / AI** | XGBoost, SHAP, pandas, NumPy |
| **IBM Technologies** | IBM Bob (used for development assistance throughout the project) |
| **Databases** | SQLite (via `grid_data.db`), CSV data pipeline |
| **Frontend Libraries** | Leaflet / react-leaflet, Recharts, TanStack Table, Zustand, Axios, React Router v7 |
| **Other** | OpenWeatherMap API, GitHub Actions, python-dotenv |

---

## 📁 Repository Structure

```
bob-ai-hackathon-telemetry-titans/
├── src/
│   ├── data/                  # Python data-generation pipeline → SQLite DB
│   │   ├── run_all.py         # Master orchestrator (runs the whole pipeline)
│   │   ├── generate_*.py      # Individual generator scripts
│   │   ├── fetch_weather.py   # Live OpenWeatherMap integration
│   │   ├── merge_to_db.py     # Loads CSVs → SQLite
│   │   ├── verify_data.py     # Data integrity checker
│   │   ├── config.py          # All tuning knobs (seeds, thresholds, paths)
│   │   ├── schema.sql         # SQLite DDL
│   │   └── requirements.txt
│   └── frontend/              # React + TypeScript dashboard
│       ├── src/
│       │   ├── pages/         # Dashboard, MapView, AssetTable, AssetDetail, …
│       │   ├── components/    # Charts, map markers, tables, UI primitives
│       │   ├── store/         # Zustand app state
│       │   ├── types/         # Domain type definitions
│       │   └── api/           # Axios API client
│       ├── package.json
│       └── vite.config.ts
├── docs/
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/
│   ├── screenshots/
│   ├── demo-video-link.txt
│   └── live-demo-url.txt
├── presentation/
├── DATA_SCHEMA.md             # Full CSV schema for the data pipeline
└── submission.yaml
```

---

## ⚡ How to Run

Full instructions are in [`docs/setup-guide.md`](docs/setup-guide.md). Quick start:

```bash
# 1. Clone the repo
git clone https://github.com/your-org/bob-ai-hackathon-telemetry-titans.git
cd bob-ai-hackathon-telemetry-titans

# 2. Generate the dataset (Python)
cd src/data
pip install -r requirements.txt
python run_all.py          # writes CSVs + grid_data.db in ~4 seconds

# 3. Run the frontend dashboard
cd ../frontend
cp .env.example .env       # default value works for local mock mode
npm install
npm run dev                # → http://localhost:5173
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/](presentation/) |

---

## ⚠️ Known Limitations

- The FastAPI backend is planned but not yet wired up — the frontend currently runs on rich mock data (`src/frontend/src/mock/`). The data pipeline generates a real SQLite database ready to be served by the backend.
- The XGBoost model scoring is embedded in the data-generation pipeline for the hackathon demo; a standalone inference endpoint is not deployed.
- Authentication/authorisation is not implemented — not production-ready.
- The app has been tested on Chrome and Firefox. Mobile layout is functional but not fully optimised.
- Live weather integration requires a free OpenWeatherMap API key (see setup guide); synthetic weather is the default.

---

## 🏅 What We're Most Proud Of

The **end-to-end data pipeline** — from realistic synthetic sensor failure signatures (temperature drift, vibration spikes, partial discharge) through risk scoring and SHAP explainability, all the way to the interactive dashboard map. The sensor physics follow real transformer-failure progression patterns, making the demo scientifically credible, not just visually polished. The tight separation between data generation, database, and UI means the system is ready to swap in real SCADA feeds with minimal changes.
