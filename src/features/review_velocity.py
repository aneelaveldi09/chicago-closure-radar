"""
Review velocity features: detect slowdowns in review activity that precede closures.

Key insight from literature: a business losing community attention (fewer reviews)
is a leading indicator of closure 3–6 months before it happens.
"""

import pandas as pd
import numpy as np
from typing import List


def compute_review_velocity(
    reviews: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    windows: List[int] = [30, 90, 180],
    baseline_days: int = 365,
) -> pd.DataFrame:
    """
    For each business, compute:
      - reviews_last_{w}d         : raw count in each window
      - velocity_{w}d             : reviews/day in window
      - velocity_ratio_{w}d       : window velocity / baseline velocity
      - velocity_drop_{w}d        : 1 if velocity_ratio < 0.5 (halved)
      - days_since_last_review    : recency signal

    Args:
        reviews: DataFrame with [business_id, date] columns
        snapshot_date: "as-of" date for feature computation
        windows: rolling window sizes in days
        baseline_days: lookback for baseline velocity
    """
    rev = reviews[reviews["date"] <= snapshot_date].copy()

    results = []
    for biz_id, grp in rev.groupby("business_id"):
        row = {"business_id": biz_id}

        baseline_start = snapshot_date - pd.Timedelta(days=baseline_days)
        baseline_reviews = grp[grp["date"] >= baseline_start]
        baseline_velocity = len(baseline_reviews) / baseline_days if baseline_days > 0 else 0

        row["baseline_velocity"] = baseline_velocity

        for w in windows:
            window_start = snapshot_date - pd.Timedelta(days=w)
            window_reviews = grp[grp["date"] >= window_start]
            count = len(window_reviews)
            velocity = count / w if w > 0 else 0

            row[f"reviews_last_{w}d"] = count
            row[f"velocity_{w}d"] = velocity
            row[f"velocity_ratio_{w}d"] = (velocity / baseline_velocity
                                            if baseline_velocity > 0 else 0.0)
            row[f"velocity_drop_{w}d"] = int(
                baseline_velocity > 0 and velocity / baseline_velocity < 0.5
            )

        # Recency
        if len(grp) > 0:
            row["days_since_last_review"] = (snapshot_date - grp["date"].max()).days
            row["total_reviews"] = len(grp)
        else:
            row["days_since_last_review"] = 9999
            row["total_reviews"] = 0

        results.append(row)

    return pd.DataFrame(results)


def compute_velocity_trend(reviews: pd.DataFrame, business_id: str,
                           snapshot_date: pd.Timestamp, n_months: int = 12) -> float:
    """
    Fit a linear regression to monthly review counts over n_months.
    Returns the slope (negative = declining trend).
    """
    rev = reviews[
        (reviews["business_id"] == business_id) &
        (reviews["date"] <= snapshot_date) &
        (reviews["date"] >= snapshot_date - pd.DateOffset(months=n_months))
    ].copy()

    if len(rev) < 3:
        return 0.0

    rev["month"] = rev["date"].dt.to_period("M")
    monthly = rev.groupby("month").size().reset_index(name="count")
    monthly["month_num"] = range(len(monthly))

    x = monthly["month_num"].values
    y = monthly["count"].values
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)
