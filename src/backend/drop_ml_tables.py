"""
drop_ml_tables.py
Drop the 3 ML-owned tables so seed.py can recreate them cleanly with proper FKs.
Run from src/backend/:  python drop_ml_tables.py
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "output" / "grid_data.db"
print(f"Connecting to: {DB}")

conn = sqlite3.connect(str(DB))
conn.execute("PRAGMA foreign_keys = OFF")   # disable FK checks for drops

for tbl in ["shap_values", "maintenance_tasks", "risk_scores"]:
    conn.execute(f"DROP TABLE IF EXISTS [{tbl}]")
    print(f"  Dropped: {tbl}")

conn.commit()
conn.close()
print("Done — run seed.py again now.")
