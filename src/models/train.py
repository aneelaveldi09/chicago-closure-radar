"""
End-to-end training pipeline for the Chicago Closure Radar.

Usage:
    python -m src.models.train \
        --features data/processed/features_2022-01-01_180d.parquet \
        --output outputs/models/
"""

import argparse
import logging
import pickle
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.models.closure_risk import prepare_xy, train_xgb, evaluate, explain_predictions

log = logging.getLogger(__name__)


def run(features_path: str, output_dir: str):
    df = pd.read_parquet(features_path)
    log.info("Loaded %d rows from %s", len(df), features_path)

    X, y = prepare_xy(df)
    log.info("Label distribution:\n%s", y.value_counts())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    log.info("Training XGBoost closure risk model...")
    clf = train_xgb(X_train, y_train)

    log.info("Evaluating on held-out test set...")
    metrics = evaluate(clf, X_test, y_test)

    # SHAP feature importance
    importance = explain_predictions(clf, X_test)
    importance.to_csv(Path(output_dir) / "feature_importance.csv", index=False)

    # Save model
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model_path = out / "closure_risk_xgb.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    log.info("Model saved to %s", model_path)

    # Save predictions on full dataset
    probs = clf.predict_proba(X)[:, 1]
    df_out = df[["business_id", "name", "label"]].copy()
    df_out["risk_score"] = probs
    df_out.to_csv(out / "predictions.csv", index=False)

    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True)
    parser.add_argument("--output", default="outputs/models/")
    args = parser.parse_args()
    run(args.features, args.output)
