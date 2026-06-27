"""
Weekly data refresh pipeline.
Pulls fresh Chicago Data Portal data, re-scores all businesses, runs alerts.

Usage:
    python -m src.pipeline.refresh           # full refresh
    python -m src.pipeline.refresh --quick   # skip re-fetching if data < 7 days old
    python -m src.pipeline.refresh --score-only  # skip fetch, just re-score
"""

import argparse
import logging
import pickle
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
log = logging.getLogger(__name__)


def needs_refresh(path: Path, max_age_days: int = 7) -> bool:
    if not path.exists():
        return True
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age > timedelta(days=max_age_days)


def run(quick: bool = False, score_only: bool = False):
    from src.data.chicago_portal import (
        fetch_business_licenses, fetch_food_inspections, build_ground_truth
    )
    from src.data.inspection_features import build_inspection_features

    raw = Path("data/raw")
    gt_dir = Path("data/ground_truth")
    proc   = Path("data/processed")

    # ── 1. Fetch fresh data ──────────────────────────────────────────────────
    if not score_only:
        force = not quick
        lic_path  = raw / "chicago_business_licenses.parquet"
        insp_path = raw / "chicago_food_inspections.parquet"

        log.info("=== Step 1: Fetching Chicago Portal data ===")
        refresh_lic  = force or needs_refresh(lic_path)
        refresh_insp = force or needs_refresh(insp_path)

        lic  = fetch_business_licenses(raw, refresh=refresh_lic)
        insp = fetch_food_inspections(raw, refresh=refresh_insp)

        log.info("=== Step 2: Rebuilding ground truth ===")
        gt = build_ground_truth(lic, insp)
        gt_dir.mkdir(parents=True, exist_ok=True)
        gt.to_parquet(gt_dir / "ground_truth.parquet", index=False)
        log.info("Ground truth: %d businesses, %d closed", len(gt), gt["is_closed"].sum())
    else:
        log.info("Score-only mode — loading existing data")
        insp = pd.read_parquet(raw / "chicago_food_inspections.parquet")
        gt   = pd.read_parquet(gt_dir / "ground_truth.parquet")

    # ── 2. Build features ────────────────────────────────────────────────────
    log.info("=== Step 3: Building features ===")
    insp["inspection_date"] = pd.to_datetime(insp["inspection_date"], errors="coerce")
    insp = insp.dropna(subset=["inspection_date"])

    snapshot = pd.Timestamp.now().normalize()
    feats = build_inspection_features(insp, snapshot)
    log.info("Features: %d businesses", len(feats))

    # ── 3. Score ─────────────────────────────────────────────────────────────
    log.info("=== Step 4: Scoring businesses ===")
    model_path = Path("outputs/models/closure_risk_xgb.pkl")
    if not model_path.exists():
        log.error("Model not found at %s — run train.py first", model_path)
        return

    with open(model_path, "rb") as f:
        clf = pickle.load(f)

    feature_cols = [c for c in feats.columns if c != "business_id"]
    X = feats[feature_cols].astype(float)
    probs = clf.predict_proba(X.fillna(X.mean()))[:, 1]

    feats["risk_score"] = probs

    # Attach names from ground truth
    gt["business_id"] = gt["business_id"].astype(str)
    feats["business_id"] = feats["business_id"].astype(str)
    out = feats.merge(gt[["business_id","dba_name","is_closed","closure_date"]],
                      on="business_id", how="left")
    out["label"] = out["is_closed"].fillna(False).astype(int)

    Path("outputs").mkdir(parents=True, exist_ok=True)
    out.to_parquet("outputs/predictions.parquet", index=False)
    log.info("Predictions saved: %d businesses scored", len(out))
    log.info("High-risk count: %d", (out["risk_score"] >= 0.66).sum())

    # ── 4. Run alerts ────────────────────────────────────────────────────────
    log.info("=== Step 5: Checking alerts ===")
    try:
        from src.pipeline.alerts import run_alerts
        run_alerts()
    except Exception as e:
        log.warning("Alert check failed (email not configured?): %s", e)

    log.info("=== Refresh complete at %s ===", datetime.now().strftime("%Y-%m-%d %H:%M"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()
    run(quick=args.quick, score_only=args.score_only)
