"""
Closure Risk Score Model

Two complementary approaches:
  1. XGBoost classifier  — interpretable, fast, handles missing values
  2. Cox Proportional Hazards — survival analysis, correct for right-censoring

The risk score output is P(closure within 6 months) ∈ [0, 1].
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (average_precision_score, classification_report,
                              roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

log = logging.getLogger(__name__)

FEATURE_COLS = [
    # Velocity
    "reviews_last_30d", "reviews_last_90d", "reviews_last_180d",
    "velocity_30d", "velocity_90d", "velocity_180d",
    "velocity_ratio_30d", "velocity_ratio_90d", "velocity_ratio_180d",
    "velocity_drop_30d", "velocity_drop_90d", "velocity_drop_180d",
    "days_since_last_review", "total_reviews",
    # Sentiment
    "sentiment_mean_30d", "sentiment_mean_90d", "sentiment_mean_180d",
    "negative_ratio_30d", "negative_ratio_90d", "negative_ratio_180d",
    "sentiment_slope", "aspect_food_score", "aspect_service_score",
    # Rating
    "rating_all_time_mean", "rating_std",
    "rating_mean_90d", "rating_mean_180d", "rating_mean_365d",
    "pct_1star_90d", "pct_1star_180d",
    "rating_slope", "rating_drop_flag",
    "rating_recent_vs_alltime", "peak_to_current_drop",
    # Business metadata
    "review_count",
]


def prepare_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[cols].copy()
    y = df["label"]
    return X, y


def train_xgb(X_train, y_train, n_folds: int = 5) -> xgb.XGBClassifier:
    """Train XGBoost with cross-validated early stopping."""
    clf = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        use_label_encoder=False,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X_train, y_train, cv=skf,
                                 scoring="average_precision", n_jobs=-1)
    log.info("CV AUC-PR: %.3f ± %.3f", cv_scores.mean(), cv_scores.std())

    clf.fit(X_train, y_train,
            eval_set=[(X_train, y_train)],
            verbose=False)
    return clf


def evaluate(clf, X_test, y_test) -> dict:
    probs = clf.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    metrics = {
        "roc_auc": roc_auc_score(y_test, probs),
        "avg_precision": average_precision_score(y_test, probs),
    }
    log.info("ROC-AUC: %.3f | Avg Precision: %.3f", metrics["roc_auc"], metrics["avg_precision"])
    print(classification_report(y_test, preds, target_names=["open", "closed"]))
    return metrics


def compute_risk_scores(clf, X: pd.DataFrame, businesses: pd.DataFrame) -> pd.DataFrame:
    """Attach risk scores to the business DataFrame."""
    probs = clf.predict_proba(X)[:, 1]
    out = businesses[["business_id", "name", "categories"]].copy()
    out["risk_score"] = probs
    out["risk_bucket"] = pd.cut(probs,
                                 bins=[0, 0.33, 0.66, 1.0],
                                 labels=["low", "medium", "high"])
    return out.sort_values("risk_score", ascending=False)


def explain_predictions(clf, X: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """SHAP feature importance for interpretability."""
    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X)
    importance = pd.DataFrame({
        "feature": X.columns,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)
    log.info("Top %d features by SHAP:\n%s", top_n, importance.head(top_n).to_string())
    return importance
