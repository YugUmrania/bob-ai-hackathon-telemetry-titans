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
from pathlib import Path

# Load .env from repo root (src/.env) so OPENWEATHERMAP_API_KEY is available
try:
    from dotenv import load_dotenv
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
    if api_key:
        print("  -> OPENWEATHERMAP_API_KEY found — fetching LIVE forecast")
        from fetch_weather import fetch_weather_alerts
        weather_df = fetch_weather_alerts()
        if weather_df.empty:
            print("  -> Live fetch returned no alerts — falling back to synthetic")
            weather_df = generate_weather_alerts()
        else:
            print(f"  -> Live fetch: {len(weather_df)} alert events")
    else:
        print("  -> No API key — using synthetic weather alerts")
        weather_df = generate_weather_alerts()
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
