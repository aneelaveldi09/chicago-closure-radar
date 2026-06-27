"""
Pull Business Licenses and Food Inspections from the City of Chicago Data Portal.
Both datasets are public (no API key required; token optional for higher rate limits).

Ground truth construction:
  - CLOSED = business has a Food Inspection result of "Out of Business"
             OR a Business License with STATUS in ('AAC', 'REV')
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

BASE_URL = "https://data.cityofchicago.org/resource"
APP_TOKEN = os.getenv("CHICAGO_PORTAL_APP_TOKEN", "")

FOOD_LICENSE_TYPES = {
    "1006",  # Retail Food Establishment
    "1016",  # Retail Food Est. - Dog-Friendly Supplemental
    "1330",  # Retail Food - Seasonal Lakefront
    "8342",  # Food - Shared Kitchen
    "1315",  # Mobile Food Dispenser
    "4405",  # Mobile Food License
}

TARGET_NAICS = {
    "722511",  # Full-Service Restaurants
    "722513",  # Limited-Service Restaurants
    "722515",  # Snack and Nonalcoholic Beverage Bars (cafes, coffee)
    "451211",  # Book Stores
}


def _get(endpoint: str, params: dict, page_size: int = 50_000) -> pd.DataFrame:
    """Paginate through a Socrata JSON endpoint and return a DataFrame."""
    headers = {"X-App-Token": APP_TOKEN} if APP_TOKEN else {}
    rows, offset = [], 0
    while True:
        p = {**params, "$limit": page_size, "$offset": offset}
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=p, headers=headers, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        rows.extend(batch)
        log.info("  fetched %d rows (offset %d)", len(batch), offset)
        if len(batch) < page_size:
            break
        offset += page_size
        time.sleep(0.3)
    return pd.DataFrame(rows)


def fetch_business_licenses(out_dir: Path, refresh: bool = False) -> pd.DataFrame:
    """
    Download Chicago Business Licenses filtered to food/cafe/bookstore types.
    Saves to out_dir/chicago_business_licenses.parquet.
    """
    out_path = out_dir / "chicago_business_licenses.parquet"
    if out_path.exists() and not refresh:
        log.info("Loading cached business licenses from %s", out_path)
        return pd.read_parquet(out_path)

    log.info("Fetching Business Licenses from Chicago Data Portal...")
    # Filter: only food-relevant license types
    license_filter = " OR ".join(f"license_code='{c}'" for c in FOOD_LICENSE_TYPES)
    df = _get("r5kz-chrr.json", {"$where": license_filter})

    # Parse dates
    for col in ["license_start_date", "expiration_date", "license_status_change_date", "date_issued"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Closure flag: AAC = cancelled mid-term, REV = revoked
    df["is_closed"] = df["license_status"].isin(["AAC", "REV"])
    df["closure_date"] = df.loc[df["is_closed"], "license_status_change_date"]

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    log.info("Saved %d license records → %s", len(df), out_path)
    return df


def fetch_food_inspections(out_dir: Path, refresh: bool = False) -> pd.DataFrame:
    """
    Download Chicago Food Inspections. 'Out of Business' result = confirmed closure.
    Saves to out_dir/chicago_food_inspections.parquet.
    """
    out_path = out_dir / "chicago_food_inspections.parquet"
    if out_path.exists() and not refresh:
        log.info("Loading cached food inspections from %s", out_path)
        return pd.read_parquet(out_path)

    log.info("Fetching Food Inspections from Chicago Data Portal...")
    df = _get("4ijn-s7e5.json", {})

    df["inspection_date"] = pd.to_datetime(df["inspection_date"], errors="coerce")
    df["is_out_of_business"] = df["results"].str.strip().str.lower() == "out of business"

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    log.info("Saved %d inspection records → %s", len(df), out_path)
    return df


def build_ground_truth(licenses: pd.DataFrame, inspections: pd.DataFrame) -> pd.DataFrame:
    """
    Merge licenses + inspections to produce a unified closure ground-truth table.

    Returns a DataFrame with columns:
        business_id, dba_name, address, zip_code, first_seen, closed, closure_date
    """
    # --- From licenses ---
    lic = licenses[["account_number", "doing_business_as_name", "address",
                    "zip_code", "license_start_date", "is_closed", "closure_date"]].copy()
    lic.rename(columns={
        "account_number": "business_id",
        "doing_business_as_name": "dba_name",
        "license_start_date": "first_seen",
    }, inplace=True)
    lic["source"] = "license"

    # --- From inspections (Out of Business) ---
    oob = inspections[inspections["is_out_of_business"]].copy()
    oob = oob[["license_", "dba_name", "address", "zip", "inspection_date"]].copy()
    oob.rename(columns={
        "license_": "business_id",
        "zip": "zip_code",
        "inspection_date": "closure_date",
    }, inplace=True)
    oob["is_closed"] = True
    oob["first_seen"] = pd.NaT
    oob["source"] = "inspection"

    combined = pd.concat([lic, oob], ignore_index=True)

    # Deduplicate: prefer license records, supplement with inspection
    closed_ids = combined[combined["is_closed"]]["business_id"].unique()
    combined["is_closed"] = combined["business_id"].isin(closed_ids)

    gt = (combined
          .sort_values(["business_id", "source"])
          .groupby("business_id", as_index=False)
          .agg({
              "dba_name": "first",
              "address": "first",
              "zip_code": "first",
              "first_seen": "min",
              "closure_date": "min",
              "is_closed": "max",
          }))

    log.info("Ground truth: %d total businesses, %d closed (%.1f%%)",
             len(gt), gt["is_closed"].sum(), 100 * gt["is_closed"].mean())
    return gt


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raw = Path("data/raw")
    lic = fetch_business_licenses(raw)
    insp = fetch_food_inspections(raw)
    gt = build_ground_truth(lic, insp)
    gt.to_parquet("data/ground_truth/ground_truth.parquet", index=False)
    print(gt["is_closed"].value_counts())
