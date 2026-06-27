"""
Master feature builder: assembles all feature modules into a single feature matrix.

Usage:
    python -m src.features.build_features \
        --snapshot 2023-06-01 \
        --horizon 180
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.features.review_velocity import compute_review_velocity
from src.features.sentiment import score_reviews, compute_sentiment_features
from src.features.rating_trajectory import compute_rating_features

log = logging.getLogger(__name__)


def build_feature_matrix(
    businesses: pd.DataFrame,
    reviews: pd.DataFrame,
    ground_truth: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    horizon_days: int = 180,
    sentiment_model: str = "vader",
) -> pd.DataFrame:
    """
    Build the full feature matrix for training or inference.

    Args:
        businesses: Yelp business records
        reviews: Yelp review records with [business_id, date, stars, text]
        ground_truth: closure ground truth with [business_id, is_closed, closure_date]
        snapshot_date: features are computed as of this date
        horizon_days: label = closed within this many days after snapshot_date
        sentiment_model: 'vader' or 'bert'

    Returns:
        DataFrame with one row per business, features + label columns.
    """
    log.info("Building features as of %s (horizon=%dd)", snapshot_date.date(), horizon_days)

    # --- Velocity features ---
    log.info("Computing review velocity features...")
    vel = compute_review_velocity(reviews, snapshot_date)

    # --- Sentiment features ---
    log.info("Scoring review sentiment (%s)...", sentiment_model)
    reviews_scored = score_reviews(reviews, model=sentiment_model)
    sent = compute_sentiment_features(reviews_scored, snapshot_date)

    # --- Rating trajectory features ---
    log.info("Computing rating trajectory features...")
    rat = compute_rating_features(reviews, snapshot_date)

    # --- Merge all feature sets ---
    feats = (businesses[["business_id", "name", "stars", "review_count",
                          "is_open", "categories", "latitude", "longitude"]]
             .merge(vel, on="business_id", how="left")
             .merge(sent, on="business_id", how="left")
             .merge(rat, on="business_id", how="left"))

    # --- Add labels from ground truth ---
    horizon_cutoff = snapshot_date + pd.Timedelta(days=horizon_days)
    gt = ground_truth[["business_id", "is_closed", "closure_date"]].copy()
    gt["label"] = (
        gt["is_closed"] &
        gt["closure_date"].between(snapshot_date, horizon_cutoff)
    ).astype(int)

    feats = feats.merge(gt[["business_id", "label", "closure_date"]],
                        on="business_id", how="left")
    feats["label"] = feats["label"].fillna(0).astype(int)

    log.info("Feature matrix: %d rows, %d columns. Positive labels: %d (%.1f%%)",
             len(feats), len(feats.columns), feats["label"].sum(),
             100 * feats["label"].mean())
    return feats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default="2022-01-01")
    parser.add_argument("--horizon", type=int, default=180)
    parser.add_argument("--sentiment", default="vader", choices=["vader", "bert"])
    args = parser.parse_args()

    biz = pd.read_parquet("data/processed/yelp_chicago_businesses.parquet")
    rev = pd.read_parquet("data/processed/yelp_chicago_reviews.parquet")
    gt = pd.read_parquet("data/ground_truth/ground_truth.parquet")

    snapshot = pd.Timestamp(args.snapshot)
    matrix = build_feature_matrix(biz, rev, gt, snapshot, args.horizon, args.sentiment)
    out_path = f"data/processed/features_{args.snapshot}_{args.horizon}d.parquet"
    matrix.to_parquet(out_path, index=False)
    print(f"Saved feature matrix to {out_path}")
