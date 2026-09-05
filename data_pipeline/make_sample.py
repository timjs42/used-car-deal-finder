import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data") / "used_cars_cleaned.csv"
OUTPUT_FILE = Path("data") / "used_cars_sample.csv"

TARGET_SAMPLE_SIZE = 8000
DESCRIPTION_MAX_CHARS = 300
RANDOM_STATE = 42


def build_sample():
    df = pd.read_csv(INPUT_FILE)
    print(f"Full cleaned dataset: {len(df):,} rows")

    sample_fraction = TARGET_SAMPLE_SIZE / len(df)
    df_sample = (
        df.groupby("manufacturer", group_keys=False)
        .apply(lambda group: group.sample(frac=sample_fraction, random_state=RANDOM_STATE))
    )

    if "description" in df_sample.columns:
        df_sample["description"] = (
            df_sample["description"].astype(str).str.slice(0, DESCRIPTION_MAX_CHARS)
        )

    df_sample = df_sample.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    df_sample.to_csv(OUTPUT_FILE, index=False)

    print(f"Sample dataset: {len(df_sample):,} rows")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_sample()