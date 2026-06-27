"""
Feature engineering directly from Chicago Food Inspection records.

Each inspection row has: results, violations (text), inspection_date, facility_type.
We derive review-analog signals purely from inspection history:
  - inspection_failure_rate       : fraction of recent inspections failed
  - violations_per_inspection     : avg violation count
  - days_since_last_inspection    : staleness / abandonment signal
  - inspection_frequency_drop     : city visits less often (bad sign)
  - consecutive_fails             : streak of failures
  - result_trend                  : numeric slope of pass(1)/fail(-1) over time
  - critical_violations_count     : count of "critical" keyword violations
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path


def count_violations(violations_str: str) -> int:
    if not isinstance(violations_str, str) or violations_str.strip() == "":
        return 0
    parts = re.split(r"\|\s*\d+\.", violations_str)
    return max(1, len(parts))


def count_critical(violations_str: str) -> int:
    if not isinstance(violations_str, str):
        return 0
    return violations_str.lower().count("critical")


def result_to_num(r: str) -> float:
    r = str(r).strip().lower()
    if r == "pass":
        return 1.0
    if r == "pass w/ conditions":
        return 0.5
    if r == "fail":
        return -1.0
    return np.nan


def build_inspection_features(
    inspections: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    windows: list = [180, 365, 730],
) -> pd.DataFrame:
    """
    Build per-business features from inspection history up to snapshot_date.
    """
    insp = inspections[
        (inspections["inspection_date"] <= snapshot_date) &
        (~inspections["is_out_of_business"])
    ].copy()

    insp["n_violations"] = insp["violations"].apply(count_violations)
    insp["n_critical"] = insp["violations"].apply(count_critical)
    insp["result_num"] = insp["results"].apply(result_to_num)

    results = []
    group_col = "license_" if "license_" in insp.columns else "license_number"

    for biz_id, grp in insp.groupby(group_col):
        grp = grp.sort_values("inspection_date")
        row = {"business_id": str(biz_id)}

        # --- All-time stats ---
        row["total_inspections"] = len(grp)
        row["all_time_fail_rate"] = (grp["results"].str.lower() == "fail").mean()
        row["all_time_violations_per_insp"] = grp["n_violations"].mean()
        row["all_time_critical_per_insp"] = grp["n_critical"].mean()

        # --- Recency ---
        row["days_since_last_inspection"] = (snapshot_date - grp["inspection_date"].max()).days

        # --- Result trend (linear slope over time) ---
        valid = grp.dropna(subset=["result_num"])
        if len(valid) >= 3:
            x = (valid["inspection_date"] - valid["inspection_date"].min()).dt.days.values.astype(float)
            y = valid["result_num"].values
            if x.max() > 0:
                row["result_trend"] = float(np.polyfit(x, y, 1)[0])
            else:
                row["result_trend"] = 0.0
        else:
            row["result_trend"] = 0.0

        # --- Consecutive fails at end ---
        recent_results = grp["results"].str.lower().tolist()[-5:]
        streak = 0
        for r in reversed(recent_results):
            if r == "fail":
                streak += 1
            else:
                break
        row["consecutive_fails"] = streak

        # --- Window features ---
        for w in windows:
            window_start = snapshot_date - pd.Timedelta(days=w)
            wgrp = grp[grp["inspection_date"] >= window_start]
            sfx = f"_{w}d"
            if len(wgrp) == 0:
                row[f"n_inspections{sfx}"] = 0
                row[f"fail_rate{sfx}"] = np.nan
                row[f"violations_per_insp{sfx}"] = np.nan
                row[f"critical_per_insp{sfx}"] = np.nan
            else:
                row[f"n_inspections{sfx}"] = len(wgrp)
                row[f"fail_rate{sfx}"] = (wgrp["results"].str.lower() == "fail").mean()
                row[f"violations_per_insp{sfx}"] = wgrp["n_violations"].mean()
                row[f"critical_per_insp{sfx}"] = wgrp["n_critical"].mean()

        # --- Inspection frequency drop (last 365d vs prior 365d) ---
        mid = snapshot_date - pd.Timedelta(days=365)
        prior_start = snapshot_date - pd.Timedelta(days=730)
        recent_count = len(grp[grp["inspection_date"] >= mid])
        prior_count = len(grp[(grp["inspection_date"] >= prior_start) &
                               (grp["inspection_date"] < mid)])
        row["inspection_freq_drop"] = int(recent_count < prior_count * 0.5)
        row["inspection_freq_ratio"] = (recent_count / prior_count
                                         if prior_count > 0 else 1.0)
        results.append(row)

    return pd.DataFrame(results)
