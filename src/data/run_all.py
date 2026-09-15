"""
run_all.py
──────────
Master orchestrator - runs every generator in sequence, then merges into SQLite.

Weather strategy (automatic):
  - If OPENWEATHERMAP_API_KEY is set in src/.env  → fetch LIVE 5-day forecast
  - Otherwise                                      → generate synthetic alerts

Usage:
    cd src/data
    python run_all.py
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from pathlib import Path

# Load .env so OPENWEATHERMAP_API_KEY is available.
# Prefer src/data/.env (where the real key lives), fall back to src/.env.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from generate_topology import generate_assets
from generate_weather import generate_weather_alerts
from generate_sensors import generate_sensors
from generate_incidents import generate_incidents
from generate_grid_zones import generate_grid_zones
from merge_to_db import merge_all
from config import OUTPUT_DIR


def main():
    t0 = time.time()
    print("=" * 60)
    print("  Telemetry Titans - Data Generation Pipeline")
    print("=" * 60)

    # 1. Grid topology (assets)
    print("\n[1/6] Generating grid topology...")
    assets_df = generate_assets()
    assets_df.to_csv(OUTPUT_DIR / "assets.csv", index=False)
    print(f"  -> Saved {OUTPUT_DIR / 'assets.csv'}")

    # 2. Weather alerts — live if API key set, synthetic otherwise
    print("\n[2/6] Fetching/generating weather alerts...")
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "").strip()

    # Always generate synthetic alerts (covers 2023-2025 past history, required by spec)
    synthetic_df = generate_weather_alerts()

    live_df = pd.DataFrame()
    if api_key:
        print("  -> OPENWEATHERMAP_API_KEY found — fetching LIVE forecast")
        from fetch_weather import fetch_weather_alerts
        live_df = fetch_weather_alerts()

    # Merge strategy:
    #   - Keep synthetic PAST events (spec rule #5 requires 2023-2025 history)
    #   - Use LIVE forecast for the upcoming window (now -> +5 days)
    if live_df.empty:
        print("  -> Live fetch returned no alerts — using synthetic weather only")
        weather_df = synthetic_df
    else:
        now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        past = synthetic_df[synthetic_df["end_time"] < now_iso]
        weather_df = pd.concat([past, live_df], ignore_index=True)
        print(f"  -> Merged: {len(past)} synthetic past + {len(live_df)} live upcoming = {len(weather_df)} rows")

    # Renumber alert_ids to spec format WX-#### , sorted by start_time
    weather_df = weather_df.sort_values("start_time").reset_index(drop=True)
    weather_df["alert_id"] = [f"WX-{i + 1:04d}" for i in range(len(weather_df))]
    weather_df = weather_df.reindex(columns=[
        "alert_id", "zone", "alert_type", "severity", "start_time", "end_time",
        "max_wind_kmh", "max_temp_c", "precipitation_mm", "source",
    ])

    weather_df.to_csv(OUTPUT_DIR / "weather_alerts.csv", index=False)
    print(f"  -> Saved {OUTPUT_DIR / 'weather_alerts.csv'} ({len(weather_df)} rows)")

    # 3. Sensor readings (depends on assets for classification)
    print("\n[3/6] Generating sensor readings...")
    sensors_df = generate_sensors(assets_df)
    sensors_df.to_csv(OUTPUT_DIR / "sensor_readings.csv", index=False)
    print(f"  -> Saved {OUTPUT_DIR / 'sensor_readings.csv'}")

    # 4. Historical incidents (depends on assets for weighting)
    print("\n[4/6] Generating historical incidents...")
    incidents_df = generate_incidents(assets_df)
    incidents_df.to_csv(OUTPUT_DIR / "historical_incidents.csv", index=False)
    print(f"  -> Saved {OUTPUT_DIR / 'historical_incidents.csv'}")

    # 5. Grid zone metadata (depends on assets for aggregation)
    print("\n[5/6] Generating grid zone metadata...")
    zones_df = generate_grid_zones(assets_df)
    zones_df.to_csv(OUTPUT_DIR / "grid_zones.csv", index=False)
    print(f"  -> Saved {OUTPUT_DIR / 'grid_zones.csv'}")

    # 6. Merge into SQLite
    print("\n[6/6] Merging into SQLite database...")
    merge_all()

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"  Pipeline complete in {elapsed:.1f}s")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
