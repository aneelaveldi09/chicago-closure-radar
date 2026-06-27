"""
Owner engagement features.

When owners stop responding to reviews, it's often because they're overwhelmed,
burned out, or already pivoting. Rising response lag → disengagement signal.

Note: Yelp Open Dataset does not include owner response timestamps directly.
This module supports enrichment from the Yelp Fusion API or scraped data.
"""

import numpy as np
import pandas as pd


def compute_owner_response_features(responses: pd.DataFrame) -> pd.DataFrame:
    """
    responses: DataFrame with [business_id, review_date, response_date]
    Returns per-business owner engagement features.
    """
    results = []
    for biz_id, grp in responses.groupby("business_id"):
        grp = grp.dropna(subset=["response_date"]).copy()
        row = {"business_id": biz_id}

        if len(grp) == 0:
            row["response_rate"] = 0.0
            row["avg_response_lag_days"] = np.nan
            row["response_lag_trend"] = 0.0
            row["has_responded_last_90d"] = 0
            results.append(row)
            continue

        all_reviews = responses[responses["business_id"] == biz_id]
        row["response_rate"] = len(grp) / len(all_reviews)

        grp["lag_days"] = (grp["response_date"] - grp["review_date"]).dt.days
        row["avg_response_lag_days"] = grp["lag_days"].mean()

        # Trend in response lag: positive slope = getting slower
        if len(grp) >= 3:
            x = (grp["review_date"] - grp["review_date"].min()).dt.days.values.astype(float)
            y = grp["lag_days"].values.astype(float)
            row["response_lag_trend"] = float(np.polyfit(x, y, 1)[0])
        else:
            row["response_lag_trend"] = 0.0

        cutoff = grp["review_date"].max() - pd.Timedelta(days=90)
        row["has_responded_last_90d"] = int(
            len(grp[grp["review_date"] >= cutoff]) > 0
        )
        results.append(row)

    return pd.DataFrame(results)
