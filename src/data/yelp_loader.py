"""
Load and filter the Yelp Open Dataset for Chicago businesses.

Download instructions:
  1. Sign up at https://business.yelp.com/data/resources/open-dataset/
     (or use Kaggle: https://www.kaggle.com/datasets/adamamer2001/yelp-complete-open-dataset-2024)
  2. Unzip into data/raw/yelp/
  3. Run this script.

Files expected:
  data/raw/yelp/yelp_academic_dataset_business.json
  data/raw/yelp/yelp_academic_dataset_review.json
  data/raw/yelp/yelp_academic_dataset_checkin.json
"""

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

CHICAGO_CITIES = {"Chicago", "Chicago Heights", "Evanston", "Oak Park", "Cicero"}
CHICAGO_STATES = {"IL"}

TARGET_CATEGORIES = [
    "coffee", "cafe", "cafes", "coffee & tea",
    "bookstore", "bookstores", "used books",
    "restaurants", "american (traditional)", "american (new)",
    "italian", "mexican", "pizza", "burgers", "sandwiches",
    "bars", "gastropubs", "wine bars",
]


def load_businesses(yelp_dir: Path) -> pd.DataFrame:
    """Load Yelp businesses filtered to Chicago food/café/bookstore establishments."""
    path = yelp_dir / "yelp_academic_dataset_business.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Yelp business file not found at {path}.\n"
            "Download the Yelp Open Dataset and unzip into data/raw/yelp/"
        )

    log.info("Loading Yelp businesses...")
    df = pd.read_json(path, lines=True)

    # Filter to Chicago area
    chi = df[df["state"].isin(CHICAGO_STATES) & df["city"].isin(CHICAGO_CITIES)].copy()
    log.info("Chicago-area businesses: %d", len(chi))

    # Filter to relevant categories
    def has_target_category(cats):
        if not isinstance(cats, str):
            return False
        cats_lower = cats.lower()
        return any(t in cats_lower for t in TARGET_CATEGORIES)

    chi = chi[chi["categories"].apply(has_target_category)].copy()
    log.info("After category filter: %d businesses", len(chi))

    # Parse hours, attributes
    chi["is_open"] = chi["is_open"].astype(bool)
    chi["review_count"] = chi["review_count"].astype(int)
    chi["stars"] = chi["stars"].astype(float)

    return chi


def load_reviews(yelp_dir: Path, business_ids: set) -> pd.DataFrame:
    """Load reviews for a set of business IDs (chunked for memory efficiency)."""
    path = yelp_dir / "yelp_academic_dataset_review.json"
    if not path.exists():
        raise FileNotFoundError(f"Yelp review file not found at {path}.")

    log.info("Loading Yelp reviews (filtering to %d businesses)...", len(business_ids))
    chunks = []
    for chunk in pd.read_json(path, lines=True, chunksize=200_000):
        filtered = chunk[chunk["business_id"].isin(business_ids)]
        if len(filtered) > 0:
            chunks.append(filtered)
        log.info("  processed chunk, kept %d reviews so far", sum(len(c) for c in chunks))

    reviews = pd.concat(chunks, ignore_index=True)
    reviews["date"] = pd.to_datetime(reviews["date"])
    log.info("Total reviews loaded: %d", len(reviews))
    return reviews


def load_checkins(yelp_dir: Path, business_ids: set) -> pd.DataFrame:
    """Load check-in data (timestamps) for the business set."""
    path = yelp_dir / "yelp_academic_dataset_checkin.json"
    if not path.exists():
        log.warning("Checkin file not found — skipping checkin features.")
        return pd.DataFrame(columns=["business_id", "date"])

    df = pd.read_json(path, lines=True)
    df = df[df["business_id"].isin(business_ids)].copy()

    # Explode comma-separated date strings into individual rows
    df["date"] = df["date"].str.split(", ")
    df = df.explode("date")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    yelp_dir = Path("data/raw/yelp")
    biz = load_businesses(yelp_dir)
    biz.to_parquet("data/processed/yelp_chicago_businesses.parquet", index=False)
    print(f"Saved {len(biz)} Chicago businesses")

    reviews = load_reviews(yelp_dir, set(biz["business_id"]))
    reviews.to_parquet("data/processed/yelp_chicago_reviews.parquet", index=False)
    print(f"Saved {len(reviews)} reviews")
