"""Data loading and preparation for the Used Car Deal Finder app."""

import pandas as pd
from pathlib import Path

DATA_PATH = Path("data") / "used_cars_sample.csv"


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the cleaned car listings sample and derive the fields the app needs."""
    df = pd.read_csv(path)

    # numeric columns
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["odometer"] = pd.to_numeric(df["odometer"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # create required fields if missing
    if "vehicle_label" not in df.columns:
        df["vehicle_label"] = (
            df["year"].astype(int).astype(str)
            + " "
            + df["manufacturer"].str.title()
            + " "
            + df["model"].str.title()
        )

    if "market_median_price" not in df.columns:
        df["market_median_price"] = df.groupby(
            ["manufacturer", "model", "year"]
        )["price"].transform("median")

    if "deal_score" not in df.columns:
        df["deal_score"] = df["market_median_price"] - df["price"]

    df["deal_score"] = pd.to_numeric(df["deal_score"], errors="coerce")
    df["market_median_price"] = pd.to_numeric(df["market_median_price"], errors="coerce")

    # drop rows with missing required fields
    df = df.dropna(
        subset=[
            "price",
            "odometer",
            "year",
            "manufacturer",
            "model",
            "state",
            "deal_score",
            "market_median_price",
        ]
    )

    # standardize text columns
    text_columns = [
        "manufacturer",
        "model",
        "condition",
        "fuel",
        "transmission",
        "drive",
        "type",
        "state",
        "region",
    ]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda value: str(value).lower().strip() if pd.notna(value) else value
            )

    # limit size for performance
    df = df.sample(n=min(50000, len(df)), random_state=42)

    # unique listing id
    df = df.reset_index(drop=True)
    df["listing_id"] = df.index

    return df