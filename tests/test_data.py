import pandas as pd
import pytest

from data import load_data

# Minimal set of columns load_data() requires to run without KeyErrors.
BASE_COLUMNS = [
    "manufacturer",
    "model",
    "year",
    "price",
    "odometer",
    "state",
    "condition",
]


@pytest.fixture
def sample_csv(tmp_path):
    """Write a small, hand-crafted listings CSV and return its path.

    Two Honda Civic 2018 listings share a manufacturer/model/year group so
    the market_median_price / deal_score grouping logic has something
    meaningful to compute. A third row (Ford) is missing its price to
    exercise the required-field drop. A fourth row has mixed-case text to
    exercise the standardization step.
    """
    df = pd.DataFrame(
        [
            {
                "manufacturer": "Honda",
                "model": "Civic",
                "year": 2018,
                "price": 15000,
                "odometer": 40000,
                "state": "CA",
                "condition": "Good",
            },
            {
                "manufacturer": "Honda",
                "model": "Civic",
                "year": 2018,
                "price": 17000,
                "odometer": 30000,
                "state": "CA",
                "condition": "good",
            },
            {
                "manufacturer": "Ford",
                "model": "Focus",
                "year": 2015,
                "price": None,  # missing price -> should be dropped
                "odometer": 60000,
                "state": "TX",
                "condition": "fair",
            },
            {
                "manufacturer": "TOYOTA",
                "model": "Camry",
                "year": 2019,
                "price": 20000,
                "odometer": 25000,
                "state": "  ny ",
                "condition": "EXCELLENT",
            },
        ]
    )
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path


def test_deal_score_is_median_minus_price(sample_csv):
    """deal_score should equal market_median_price - price for each row."""
    result = load_data(sample_csv)

    civics = result[result["model"] == "civic"]
    assert len(civics) == 2

    # Median of [15000, 17000] is 16000:
    # cheaper listing (15000) should show a positive deal score of 1000
    # pricier listing (17000) should show a negative deal score of -1000
    cheap_listing = civics[civics["price"] == 15000].iloc[0]
    pricey_listing = civics[civics["price"] == 17000].iloc[0]

    assert cheap_listing["market_median_price"] == 16000
    assert cheap_listing["deal_score"] == 1000
    assert pricey_listing["deal_score"] == -1000


def test_rows_missing_required_fields_are_dropped(sample_csv):
    """A row missing a required field (price) should not appear in the output."""
    result = load_data(sample_csv)

    assert "ford" not in result["manufacturer"].values
    assert len(result) == 3  # started with 4 rows, one dropped


def test_text_columns_are_lowercased_and_stripped(sample_csv):
    """Text fields should be normalized to lowercase with whitespace trimmed."""
    result = load_data(sample_csv)

    assert set(result["manufacturer"].unique()) == {"honda", "toyota"}
    assert set(result["condition"].unique()) == {"good", "excellent"}
    assert "ny" in result["state"].values  # "  ny " -> "ny"


def test_vehicle_label_is_generated_when_missing(sample_csv):
    """vehicle_label should combine year, manufacturer, and model, title-cased."""
    result = load_data(sample_csv)

    toyota_row = result[result["manufacturer"] == "toyota"].iloc[0]
    assert toyota_row["vehicle_label"] == "2019 Toyota Camry"


def test_listing_id_is_unique_and_zero_indexed(sample_csv):
    """Every row should get a unique listing_id starting from 0."""
    result = load_data(sample_csv)

    assert result["listing_id"].is_unique
    assert sorted(result["listing_id"]) == list(range(len(result)))
