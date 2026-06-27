"""
Chicago Closure Radar — FastAPI Risk Score API
Deploy on Railway. Provides a REST API for risk scores.

Endpoints:
  GET  /                        → health check
  GET  /businesses              → paginated list with risk scores
  GET  /businesses/{id}         → single business detail
  POST /search                  → search by name
  GET  /top-risk?n=20           → top N highest-risk businesses
  GET  /stats                   → city-wide summary stats
"""

import os
import pickle
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

warnings.filterwarnings("ignore")

app = FastAPI(
    title="Chicago Closure Radar API",
    description="Real-time closure risk scores for Chicago food businesses.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PRED_PATH = Path(os.getenv("PREDICTIONS_PATH", "outputs/predictions.parquet"))
_cache: dict = {}


def get_predictions() -> pd.DataFrame:
    if "df" not in _cache:
        if not PRED_PATH.exists():
            raise RuntimeError(f"Predictions file not found: {PRED_PATH}")
        df = pd.read_parquet(PRED_PATH)
        df["risk_bucket"] = pd.cut(
            df["risk_score"], bins=[0, 0.33, 0.66, 1.0],
            labels=["low", "medium", "high"]
        ).astype(str)
        _cache["df"] = df
    return _cache["df"]


# ── Response models ───────────────────────────────────────────────────────────

class BusinessRisk(BaseModel):
    business_id: str
    name: Optional[str]
    risk_score: float
    risk_bucket: str
    days_since_last_inspection: Optional[float]
    all_time_fail_rate: Optional[float]
    all_time_violations_per_insp: Optional[float]
    consecutive_fails: Optional[float]
    result_trend: Optional[float]
    address: Optional[str]
    zip_code: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class StatsResponse(BaseModel):
    total_businesses: int
    high_risk: int
    medium_risk: int
    low_risk: int
    high_risk_pct: float
    confirmed_closed: int
    model_roc_auc: float


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "operational", "service": "Chicago Closure Radar API"}


@app.get("/stats", response_model=StatsResponse, tags=["Analytics"])
def get_stats():
    df = get_predictions()
    return StatsResponse(
        total_businesses=len(df),
        high_risk=int((df["risk_bucket"] == "high").sum()),
        medium_risk=int((df["risk_bucket"] == "medium").sum()),
        low_risk=int((df["risk_bucket"] == "low").sum()),
        high_risk_pct=round(float((df["risk_bucket"] == "high").mean()), 4),
        confirmed_closed=int(df["label"].sum()) if "label" in df.columns else 0,
        model_roc_auc=0.807,
    )


@app.get("/businesses", tags=["Businesses"])
def list_businesses(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    risk_bucket: Optional[str] = Query(None, description="low | medium | high"),
    zip_code: Optional[str] = None,
    sort_by: str = Query("risk_score", description="risk_score | name"),
    order: str = Query("desc", description="asc | desc"),
):
    df = get_predictions()

    if risk_bucket:
        df = df[df["risk_bucket"] == risk_bucket.lower()]
    if zip_code:
        if "zip_code" in df.columns:
            df = df[df["zip_code"].astype(str).str.startswith(zip_code)]

    ascending = order == "asc"
    sort_col = "dba_name" if sort_by == "name" else "risk_score"
    if sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=ascending)

    total = len(df)
    start = (page - 1) * page_size
    page_df = df.iloc[start:start + page_size]

    cols = ["business_id", "dba_name", "risk_score", "risk_bucket"]
    opt  = ["days_since_last_inspection", "all_time_fail_rate",
            "all_time_violations_per_insp", "address", "zip_code", "latitude", "longitude"]
    cols += [c for c in opt if c in df.columns]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": page_df[cols].fillna("").to_dict("records"),
    }


@app.get("/businesses/{business_id}", tags=["Businesses"])
def get_business(business_id: str):
    df = get_predictions()
    row = df[df["business_id"].astype(str) == business_id]
    if len(row) == 0:
        raise HTTPException(404, detail=f"Business {business_id!r} not found")

    r = row.iloc[0]
    detail_cols = [c for c in df.columns
                   if c not in ["index"] and not c.startswith(":")]
    return r[detail_cols].fillna("").to_dict()


@app.post("/search", tags=["Businesses"])
def search_businesses(body: SearchRequest):
    df = get_predictions()
    if "dba_name" not in df.columns:
        raise HTTPException(500, "Name column not available")

    mask = df["dba_name"].str.contains(body.query, case=False, na=False)
    results = df[mask].nlargest(body.limit, "risk_score")

    cols = ["business_id", "dba_name", "risk_score", "risk_bucket"]
    opt  = ["days_since_last_inspection", "all_time_fail_rate", "address", "zip_code", "latitude", "longitude"]
    cols += [c for c in opt if c in df.columns]
    return results[cols].fillna("").to_dict("records")


@app.get("/top-risk", tags=["Analytics"])
def top_risk(n: int = Query(20, ge=1, le=100)):
    df = get_predictions()
    top = df.nlargest(n, "risk_score")
    cols = ["business_id", "dba_name", "risk_score", "risk_bucket"]
    opt  = ["days_since_last_inspection", "all_time_fail_rate",
            "all_time_violations_per_insp", "address", "zip_code", "latitude", "longitude"]
    cols += [c for c in opt if c in df.columns]
    return top[cols].fillna("").to_dict("records")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
