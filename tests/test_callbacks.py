from callbacks import build_query_from_filters, parse_filters_from_query

YEAR_MIN, YEAR_MAX = 1990, 2021
MILEAGE_MIN, MILEAGE_MAX = 0, 300_000


def test_parse_filters_from_query_empty_string_gives_defaults():
    result = parse_filters_from_query("", YEAR_MIN, YEAR_MAX, MILEAGE_MIN, MILEAGE_MAX)

    assert result == (
        None,
        None,
        None,
        [],
        None,
        "all",
        [YEAR_MIN, YEAR_MAX],
        [MILEAGE_MIN, MILEAGE_MAX],
    )


def test_parse_filters_from_query_reads_all_fields():
    query = "manufacturer=honda&model=civic&state=ca&condition=good,excellent&fuel=gas"
    query += "&transmission=automatic&year_min=2015&year_max=2020"
    query += "&mileage_min=10000&mileage_max=50000"

    result = parse_filters_from_query(query, YEAR_MIN, YEAR_MAX, MILEAGE_MIN, MILEAGE_MAX)

    assert result == (
        "honda",
        "civic",
        "ca",
        ["good", "excellent"],
        "gas",
        "automatic",
        [2015, 2020],
        [10000, 50000],
    )


def test_parse_filters_from_query_clips_out_of_range_bounds():
    query = "year_min=1900&year_max=2999&mileage_min=-5&mileage_max=999999999"

    result = parse_filters_from_query(query, YEAR_MIN, YEAR_MAX, MILEAGE_MIN, MILEAGE_MAX)

    assert result[6] == [YEAR_MIN, YEAR_MAX]
    assert result[7] == [MILEAGE_MIN, MILEAGE_MAX]


def test_build_query_from_filters_omits_unset_filters():
    query = build_query_from_filters(
        None,
        None,
        None,
        [],
        None,
        "all",
        [YEAR_MIN, YEAR_MAX],
        [MILEAGE_MIN, MILEAGE_MAX],
        YEAR_MIN,
        YEAR_MAX,
        MILEAGE_MIN,
        MILEAGE_MAX,
    )

    assert query == ""


def test_build_query_from_filters_round_trips_through_parse():
    query = build_query_from_filters(
        "honda",
        "civic",
        "ca",
        ["good", "excellent"],
        "gas",
        "automatic",
        [2015, 2020],
        [10000, 50000],
        YEAR_MIN,
        YEAR_MAX,
        MILEAGE_MIN,
        MILEAGE_MAX,
    )

    parsed = parse_filters_from_query(
        query.lstrip("?"), YEAR_MIN, YEAR_MAX, MILEAGE_MIN, MILEAGE_MAX
    )

    assert parsed == (
        "honda",
        "civic",
        "ca",
        ["good", "excellent"],
        "gas",
        "automatic",
        [2015, 2020],
        [10000, 50000],
    )
