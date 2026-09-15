from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.db.models import Asset, RiskScore, ShapValue, SensorReading
from app.models.schemas import AssetOut, SensorReadingOut, ShapValueOut

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


def _build_asset_out(asset: Asset, rs: RiskScore, shap_rows=None) -> AssetOut:
    risk_level_upper = (rs.risk_level if rs else "LOW")
    return AssetOut(
        asset_id=asset.asset_id,
        id=asset.asset_id,                           # frontend uses .id
        name=asset.asset_id,                         # frontend uses .name
        asset_type=asset.asset_type,
        zone=asset.zone,
        lat=asset.lat,
        lng=asset.lng,
        risk_score=rs.risk_score if rs else 0.0,
        priority_score=rs.priority_score if rs else 0.0,
        risk_level=risk_level_upper.lower(),         # frontend expects lowercase
        customers_served=asset.customers_served or 0,
        has_critical_facility=asset.has_critical_facility or 0,
        last_inspected=asset.last_inspected,
        install_year=asset.install_year,
        voltage_kv=asset.voltage_kv,
        manufacturer=asset.manufacturer,
        capacity_mva=asset.capacity_mva,
        shap_values=[
            ShapValueOut(feature=s.feature, contribution=s.contribution)
            for s in (shap_rows or [])
        ] or None,
    )


@router.get("", response_model=List[AssetOut])
def list_assets(
    risk_level: Optional[str] = Query(None, description="Filter by CRITICAL|HIGH|MEDIUM|LOW"),
    zone: Optional[str] = Query(None, description="Filter by zone name"),
    sort: str = Query("priority_score", description="Field to sort by"),
    order: str = Query("desc", description="asc or desc"),
    limit: Optional[int] = Query(None, description="Max results"),
    db: Session = Depends(get_db),
):
    """Return all assets with their risk scores, optionally filtered and sorted."""
    q = (
        db.query(Asset, RiskScore)
        .outerjoin(RiskScore, Asset.asset_id == RiskScore.asset_id)
    )

    if risk_level:
        q = q.filter(RiskScore.risk_level == risk_level.upper())
    if zone:
        q = q.filter(Asset.zone == zone)

    # Sorting
    sort_col_map = {
        "risk_score":     RiskScore.risk_score,
        "priority_score": RiskScore.priority_score,
        "customers_served": Asset.customers_served,
        "asset_id":       Asset.asset_id,
        "zone":           Asset.zone,
    }
    col = sort_col_map.get(sort, RiskScore.priority_score)
    q = q.order_by(col.desc() if order == "desc" else col.asc())

    if limit:
        q = q.limit(limit)

    results = q.all()
    return [_build_asset_out(a, rs) for a, rs in results]


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """Return a single asset with risk score + SHAP explanations."""
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    rs = db.get(RiskScore, asset_id)
    shap_rows = (
        db.query(ShapValue)
        .filter(ShapValue.asset_id == asset_id)
        .order_by(ShapValue.contribution.desc())
        .all()
    )
    return _build_asset_out(asset, rs, shap_rows)


@router.get("/{asset_id}/sensors", response_model=List[SensorReadingOut])
def get_sensor_readings(
    asset_id: str,
    days: int = Query(30, description="How many days of history to return"),
    limit: Optional[int] = Query(None, description="Max readings to return"),
    db: Session = Depends(get_db),
):
    """Return sensor time-series for one asset (last N days, chronological)."""
    if not db.get(Asset, asset_id):
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    max_rows = limit or (days * 24)
    rows = (
        db.query(SensorReading)
        .filter(SensorReading.asset_id == asset_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(max_rows)
        .all()
    )
    return [SensorReadingOut.model_validate(r) for r in reversed(rows)]

