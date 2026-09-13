from pathlib import Path

import pandas as pd

# file paths

DATA_DIR = Path("data")
RAW_FILE = DATA_DIR / "used_cars.zip"
CLEAN_FILE = DATA_DIR / "used_cars_cleaned.csv"

# columns to keep

COLUMNS_TO_KEEP = [
    "url",
    "region",
    "price",
    "year",
    "manufacturer",
    "model",
    "condition",
    "fuel",
    "odometer",
    "transmission",
    "drive",
    "type",
    "state",
    "lat",
    "long",
    "posting_date",
    "description",
]

# function


def clean_used_car_data():
    print("Loading raw dataset...")

    df = pd.read_csv(
        RAW_FILE,
        compression="zip",
        usecols=lambda col: col in COLUMNS_TO_KEEP,
        low_memory=False,
    )

    print(f"Original rows: {len(df):,}")

    # drop rows
    df = df.dropna(
        subset=[
            "price",
            "year",
            "manufacturer",
            "model",
            "odometer",
            "state",
        ]
    )

    # convert numeric fields
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["odometer"] = pd.to_numeric(df["odometer"], errors="coerce")

    df = df.dropna(subset=["price", "year", "odometer"])

    # remove unrealistic outliers
    df = df[
        (df["price"] >= 1000)
        & (df["price"] <= 100000)
        & (df["year"] >= 1990)
        & (df["year"] <= 2025)
        & (df["odometer"] >= 1000)
        & (df["odometer"] <= 300000)
    ]

    # clean text columns
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
            df[col] = df[col].astype(str).str.lower().str.strip()

    # create vehicle age
    df["vehicle_age"] = 2025 - df["year"]

    # create display label
    df["vehicle_label"] = (
        df["year"].astype(int).astype(str)
        + " "
        + df["manufacturer"].str.title()
        + " "
        + df["model"].str.title()
    )

    # estimate market median price
    group_cols = ["manufacturer", "model", "year"]

    df["market_median_price"] = df.groupby(group_cols)["price"].transform("median")

    # deal score: positive means listed below comparable market median
    df["deal_score"] = df["market_median_price"] - df["price"]

    # drop rows where deal score could not be calculated
    df = df.dropna(subset=["deal_score"])

    # sort by strongest apparent deal
    df = df.sort_values("deal_score", ascending=False)

    print(f"Cleaned rows: {len(df):,}")

    # save cleaned file
    df.to_csv(CLEAN_FILE, index=False)

    print(f"Cleaned data saved to: {CLEAN_FILE}")


if __name__ == "__main__":
    clean_used_car_data()
