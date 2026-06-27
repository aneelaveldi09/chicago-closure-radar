"""
Sentiment features from review text.

Two modes:
  - 'vader'  : fast, no GPU needed, good for short reviews (default)
  - 'bert'   : slower, better accuracy, uses cardiffnlp/twitter-roberta-base-sentiment

Key features:
  - sentiment_mean_{w}d     : average compound score in window
  - sentiment_trend         : slope of compound scores over time
  - negative_ratio_{w}d     : fraction of reviews with compound < -0.05
  - aspect_food_score       : avg sentiment for food-related sentences
  - aspect_service_score    : avg sentiment for service-related sentences
"""

import logging
from typing import List

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def _vader_scores(texts: List[str]) -> List[float]:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()
    return [sia.polarity_scores(t)["compound"] for t in texts]


def _bert_scores(texts: List[str], batch_size: int = 64) -> List[float]:
    from transformers import pipeline
    pipe = pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        truncation=True,
        max_length=512,
    )
    label_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    scores = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        outputs = pipe(batch)
        scores.extend(label_map.get(o["label"].lower(), 0.0) for o in outputs)
    return scores


def score_reviews(reviews: pd.DataFrame, model: str = "vader") -> pd.DataFrame:
    """
    Add a 'sentiment_score' column (compound score in [-1, 1]) to the reviews DataFrame.
    """
    texts = reviews["text"].fillna("").tolist()
    if model == "bert":
        log.info("Running BERT sentiment on %d reviews...", len(texts))
        scores = _bert_scores(texts)
    else:
        log.info("Running VADER sentiment on %d reviews...", len(texts))
        scores = _vader_scores(texts)
    reviews = reviews.copy()
    reviews["sentiment_score"] = scores
    return reviews


def compute_sentiment_features(
    reviews: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    windows: List[int] = [30, 90, 180],
) -> pd.DataFrame:
    """
    Compute per-business sentiment features as of snapshot_date.

    Requires reviews to already have a 'sentiment_score' column.
    """
    if "sentiment_score" not in reviews.columns:
        raise ValueError("Run score_reviews() first to add sentiment_score column.")

    rev = reviews[reviews["date"] <= snapshot_date].copy()
    results = []

    for biz_id, grp in rev.groupby("business_id"):
        grp = grp.sort_values("date")
        row = {"business_id": biz_id}

        for w in windows:
            window_start = snapshot_date - pd.Timedelta(days=w)
            window = grp[grp["date"] >= window_start]
            if len(window) == 0:
                row[f"sentiment_mean_{w}d"] = np.nan
                row[f"negative_ratio_{w}d"] = np.nan
            else:
                row[f"sentiment_mean_{w}d"] = window["sentiment_score"].mean()
                row[f"negative_ratio_{w}d"] = (window["sentiment_score"] < -0.05).mean()

        # Sentiment trend: linear slope over all historical reviews
        if len(grp) >= 5:
            x = (grp["date"] - grp["date"].min()).dt.days.values
            y = grp["sentiment_score"].values
            row["sentiment_slope"] = float(np.polyfit(x, y, 1)[0])
        else:
            row["sentiment_slope"] = 0.0

        # Aspect-based: food vs. service keywords
        food_kw = {"food", "taste", "flavor", "dish", "menu", "cook", "chef", "meal"}
        svc_kw = {"service", "staff", "waiter", "server", "rude", "slow", "wait", "attitude"}

        def aspect_score(kw_set):
            mask = grp["text"].fillna("").str.lower().apply(
                lambda t: any(k in t for k in kw_set)
            )
            sub = grp[mask]
            return sub["sentiment_score"].mean() if len(sub) > 0 else np.nan

        row["aspect_food_score"] = aspect_score(food_kw)
        row["aspect_service_score"] = aspect_score(svc_kw)

        results.append(row)

    return pd.DataFrame(results)
