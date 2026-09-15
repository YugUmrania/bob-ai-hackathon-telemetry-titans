"""
prediction.py — Train XGBoost model on sensor + incident data, score all
assets 0-100, compute SHAP values, and persist results to the DB.
"""

import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

log = logging.getLogger(__name__)

# Model saved alongside data team's DB output
MODEL_PATH = Path(__file__).resolve().parents[4] / "data" / "output" / "gridhealth_model.pkl"

# Sensor features used by the model
FEATURE_COLS = [
    "temperature_c_mean",
    "temperature_c_max",
    "vibration_mm_s_mean",
    "vibration_mm_s_max",
    "oil_quality_index_mean",
    "oil_quality_index_min",
    "partial_discharge_mv_mean",
    "partial_discharge_mv_max",
    "load_percent_mean",
    "asset_age_years",
    "incident_count_past_year",
]


# ── Feature engineering ───────────────────────────────────────────────────────

def _build_feature_matrix(db: Session) -> pd.DataFrame:
    """Aggregate sensor readings and incidents into one row per asset."""

    # 1. Get all assets
    assets_df = pd.read_sql(text("SELECT * FROM assets"), db.get_bind())
    if assets_df.empty:
        return pd.DataFrame()

    # 2. Aggregate last-30-day sensor readings per asset
    sensor_sql = text("""
        SELECT
            asset_id,
            AVG(temperature_c)          AS temperature_c_mean,
            MAX(temperature_c)          AS temperature_c_max,
            AVG(vibration_mm_s)         AS vibration_mm_s_mean,
            MAX(vibration_mm_s)         AS vibration_mm_s_max,
            AVG(oil_quality_index)      AS oil_quality_index_mean,
            MIN(oil_quality_index)      AS oil_quality_index_min,
            AVG(partial_discharge_mv)   AS partial_discharge_mv_mean,
            MAX(partial_discharge_mv)   AS partial_discharge_mv_max,
            AVG(load_percent)           AS load_percent_mean
        FROM sensor_readings
        GROUP BY asset_id
    """)
    sensor_df = pd.read_sql(sensor_sql, db.get_bind())

    # 3. Count incidents per asset in the last 12 months
    incident_sql = text("""
        SELECT asset_id, COUNT(*) AS incident_count_past_year
        FROM historical_incidents
        WHERE incident_date >= date('now', '-1 year')
        GROUP BY asset_id
    """)
    incident_df = pd.read_sql(incident_sql, db.get_bind())

    # 4. Merge everything
    df = assets_df.merge(sensor_df, on="asset_id", how="left")
    df = df.merge(incident_df, on="asset_id", how="left")

    # 5. Derived features
    current_year = datetime.now().year
    df["asset_age_years"] = current_year - df["install_year"].fillna(2010)
    df["incident_count_past_year"] = df["incident_count_past_year"].fillna(0)

    # 6. Fill remaining NaN sensor values with safe defaults (healthy-range midpoints)
    defaults = {
        "temperature_c_mean": 60.0,
        "temperature_c_max": 70.0,
        "vibration_mm_s_mean": 3.0,
        "vibration_mm_s_max": 4.0,
        "oil_quality_index_mean": 65.0,
        "oil_quality_index_min": 55.0,
        "partial_discharge_mv_mean": 100.0,
        "partial_discharge_mv_max": 150.0,
        "load_percent_mean": 60.0,
    }
    for col, val in defaults.items():
        df[col] = df[col].fillna(val)

    return df


# ── Synthetic label generation (for training when no real labels exist) ───────

def _make_synthetic_labels(df: pd.DataFrame) -> np.ndarray:
    """
    Rule-based failure probability used as training labels.
    In a production system these would come from actual outage records.
    """
    score = np.zeros(len(df))

    # Temperature pressure (0-35 pts)
    score += np.clip((df["temperature_c_max"] - 60) / 25 * 35, 0, 35).values

    # Vibration pressure (0-20 pts)
    score += np.clip((df["vibration_mm_s_max"] - 4) / 4 * 20, 0, 20).values

    # Oil quality degradation (0-20 pts — inverted: lower oil = higher risk)
    score += np.clip((70 - df["oil_quality_index_min"]) / 60 * 20, 0, 20).values

    # Partial discharge (0-15 pts)
    score += np.clip((df["partial_discharge_mv_max"] - 150) / 400 * 15, 0, 15).values

    # Asset age (0-10 pts)
    score += np.clip(df["asset_age_years"] / 30 * 10, 0, 10).values

    return np.clip(score, 0, 100)


# ── Train / load model ────────────────────────────────────────────────────────

def get_or_train_model(df: pd.DataFrame):
    """Load saved model or train a new one."""
    import xgboost as xgb

    X = df[FEATURE_COLS].values

    if MODEL_PATH.exists():
        log.info("Loading existing model from %s", MODEL_PATH)
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        return model, X

    log.info("Training new XGBoost model…")
    y = _make_synthetic_labels(df)

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X, y)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    log.info("Model saved to %s", MODEL_PATH)

    return model, X


# ── SHAP values ───────────────────────────────────────────────────────────────

def _compute_shap(model, X: np.ndarray) -> np.ndarray:
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        return shap_values
    except Exception as exc:
        log.warning("SHAP computation failed (%s) — using zero contributions", exc)
        return np.zeros_like(X)


# ── Main entry point ──────────────────────────────────────────────────────────

def score_all_assets(db: Session):
    """Build features, run model, persist RiskScore + ShapValue rows."""
    from app.db.models import RiskScore, ShapValue

    df = _build_feature_matrix(db)
    if df.empty:
        log.warning("No assets found — skipping risk scoring")
        return

    model, X = get_or_train_model(df)
    raw_scores = model.predict(X).clip(0, 100)
    shap_matrix = _compute_shap(model, X)

    now_iso = datetime.now(timezone.utc).isoformat()

    # Delete existing scores before re-inserting
    db.query(RiskScore).delete()
    db.query(ShapValue).delete()
    db.commit()

    for i, row in df.iterrows():
        asset_id = row["asset_id"]
        risk_score = float(raw_scores[i])

        # Priority score formula (see BACKEND_SPEC.md)
        max_customers = df["customers_served"].max() or 1
        customers_norm = (row["customers_served"] / max_customers) * 100
        has_critical = int(row.get("has_critical_facility", 0))

        # Weather risk bonus: +1 if active alert in this zone
        weather_bonus = _weather_bonus(db, row["zone"])

        priority_score = (
            risk_score * 0.50
            + customers_norm * 0.25
            + has_critical * 15
            + weather_bonus * 10
        )
        priority_score = float(np.clip(priority_score, 0, 100))

        risk_level = _risk_level(priority_score)

        db.add(RiskScore(
            asset_id=asset_id,
            risk_score=round(risk_score, 2),
            priority_score=round(priority_score, 2),
            risk_level=risk_level,
            computed_at=now_iso,
        ))

        # SHAP values
        shap_row = shap_matrix[i] if shap_matrix.ndim == 2 else shap_matrix
        for j, feat in enumerate(FEATURE_COLS):
            db.add(ShapValue(
                asset_id=asset_id,
                feature=feat,
                contribution=round(float(shap_row[j]), 4),
            ))

    db.commit()
    log.info("Scored %d assets", len(df))


def _weather_bonus(db: Session, zone: str) -> int:
    """Return 1 if there is an active HIGH/CRITICAL weather alert in this zone."""
    from app.db.models import WeatherAlert
    now_iso = datetime.now(timezone.utc).isoformat()
    alert = (
        db.query(WeatherAlert)
        .filter(
            WeatherAlert.zone == zone,
            WeatherAlert.severity.in_(["HIGH", "CRITICAL"]),
            WeatherAlert.start_time <= now_iso,
        )
        .first()
    )
    return 1 if alert else 0


def _risk_level(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"
