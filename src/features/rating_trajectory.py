"""
Rating trajectory features: detect downward bends in star ratings.

A business that once had 4.5 stars drifting toward 3.5 over 6 months is a
leading signal — the aggregate star rating displayed publicly lags behind this.
"""

import numpy as np
import pandas as pd
from typing import List


def compute_rating_features(
    reviews: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    windows: List[int] = [90, 180, 365],
    min_reviews: int = 5,
) -> pd.DataFrame:
    """
    Per-business rating features:
      - rating_mean_{w}d          : avg star rating in window
      - rating_slope              : linear trend slope (negative = declining)
      - rating_drop_flag          : 1 if last-90d avg < all-time avg by > 0.5 stars
      - rating_std                : volatility (inconsistent = risky)
      - pct_1star_{w}d            : fraction of 1-star reviews in window
      - peak_to_current_drop      : peak rolling avg - current rolling avg
    """
    rev = reviews[reviews["date"] <= snapshot_date].copy()
    results = []

    for biz_id, grp in rev.groupby("business_id"):
        grp = grp.sort_values("date")
        row = {"business_id": biz_id}

        all_time_mean = grp["stars"].mean()
        row["rating_all_time_mean"] = all_time_mean
        row["rating_std"] = grp["stars"].std() if len(grp) > 1 else 0.0

        for w in windows:
            window_start = snapshot_date - pd.Timedelta(days=w)
            window = grp[grp["date"] >= window_start]
            if len(window) < min_reviews:
                row[f"rating_mean_{w}d"] = np.nan
                row[f"pct_1star_{w}d"] = np.nan
            else:
                row[f"rating_mean_{w}d"] = window["stars"].mean()
                row[f"pct_1star_{w}d"] = (window["stars"] == 1).mean()

        # Rating slope across last 365 days
        last_year = grp[grp["date"] >= snapshot_date - pd.Timedelta(days=365)]
        if len(last_year) >= min_reviews:
            x = (last_year["date"] - last_year["date"].min()).dt.days.values.astype(float)
            y = last_year["stars"].values.astype(float)
            row["rating_slope"] = float(np.polyfit(x, y, 1)[0])
        else:
            row["rating_slope"] = 0.0

        # Drop flag: recent 90d avg < all-time avg by > 0.5 stars
        recent_90 = grp[grp["date"] >= snapshot_date - pd.Timedelta(days=90)]
        if len(recent_90) >= min_reviews:
            recent_mean = recent_90["stars"].mean()
            row["rating_drop_flag"] = int(all_time_mean - recent_mean > 0.5)
            row["rating_recent_vs_alltime"] = recent_mean - all_time_mean
        else:
            row["rating_drop_flag"] = 0
            row["rating_recent_vs_alltime"] = 0.0

        # Peak-to-current: 6-month rolling max vs. last 90d
        grp_indexed = grp.set_index("date")["stars"].resample("ME").mean().dropna()
        if len(grp_indexed) >= 3:
            peak = grp_indexed.rolling(3, min_periods=1).mean().max()
            current = grp_indexed.iloc[-3:].mean()
            row["peak_to_current_drop"] = float(peak - current)
        else:
            row["peak_to_current_drop"] = 0.0

        results.append(row)

    return pd.DataFrame(results)
