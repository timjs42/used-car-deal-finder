import pandas as pd
from dash import dash_table, dcc, html


def build_layout(df: pd.DataFrame) -> html.Div:
    """Build the app's layout using the loaded dataframe to populate filter options."""

    manufacturer_options = sorted(df["manufacturer"].dropna().unique())
    state_options = sorted(df["state"].dropna().unique())

    condition_options = (
        sorted(df["condition"].dropna().unique()) if "condition" in df.columns else []
    )

    fuel_options = sorted(df["fuel"].dropna().unique()) if "fuel" in df.columns else []

    year_min = int(df["year"].min())
    year_max = int(df["year"].max())

    mileage_min = int(df["odometer"].min())
    mileage_max = int(df["odometer"].max())

    return html.Div(
        className="app-container",
        children=[
            dcc.Store(id="theme-store", storage_type="local", data="light"),
            html.Div(
                className="header",
                children=[
                    html.Button(
                        "\U0001f319 Dark Mode",
                        id="theme-toggle",
                        className="theme-toggle",
                        n_clicks=0,
                    ),
                    html.H1("Used Car Deal Finder"),
                    html.P(
                        "This dashboard helps users explore used car listings and identify "
                        "potential deals based on price, mileage, year, condition, fuel type, "
                        "transmission, and location."
                    ),
                    html.P(
                        "A positive deal score means the vehicle is listed below the median "
                        "price of similar vehicles with the same manufacturer, model, and year. "
                        "Click a point or bar in the charts to view listing details."
                    ),
                ],
            ),
            html.Div(
                className="main-layout",
                children=[
                    dcc.Store(id="sidebar-open", data=True),
                    html.Div(
                        className="sidebar",
                        children=[
                            html.Button(
                                "Hide Filters",
                                id="sidebar-toggle",
                                className="sidebar-toggle",
                                n_clicks=0,
                                **{"aria-expanded": "true", "aria-controls": "filters-panel"},
                            ),
                            html.Div(
                                id="filters-panel",
                                className="filters-panel",
                                children=[
                                    html.H3("Filters"),
                                    html.Label("Manufacturer", htmlFor="manufacturer-filter"),
                                    dcc.Dropdown(
                                        id="manufacturer-filter",
                                        options=[
                                            {"label": m.title(), "value": m}
                                            for m in manufacturer_options
                                        ],
                                        value=None,
                                        placeholder="Select a manufacturer",
                                        clearable=True,
                                    ),
                                    html.Label("Model Keyword", htmlFor="model-search"),
                                    dcc.Input(
                                        id="model-search",
                                        type="text",
                                        placeholder="Example: civic, camry, accord",
                                        debounce=True,
                                        style={
                                            "width": "100%",
                                            "padding": "10px",
                                            "borderRadius": "6px",
                                            "border": "1px solid #d1d5db",
                                            "boxSizing": "border-box",
                                        },
                                    ),
                                    html.Label("State", htmlFor="state-filter"),
                                    dcc.Dropdown(
                                        id="state-filter",
                                        options=[
                                            {"label": s.upper(), "value": s} for s in state_options
                                        ],
                                        value=None,
                                        placeholder="Select a state",
                                        clearable=True,
                                    ),
                                    html.Label("Condition"),
                                    dcc.Checklist(
                                        id="condition-filter",
                                        options=[
                                            {"label": c.title(), "value": c}
                                            for c in condition_options
                                        ],
                                        value=[],
                                        inline=False,
                                    ),
                                    html.Label("Fuel Type", htmlFor="fuel-filter"),
                                    dcc.Dropdown(
                                        id="fuel-filter",
                                        options=[
                                            {"label": f.title(), "value": f} for f in fuel_options
                                        ],
                                        value=None,
                                        placeholder="Select fuel type",
                                        clearable=True,
                                    ),
                                    html.Label("Transmission"),
                                    dcc.RadioItems(
                                        id="transmission-filter",
                                        options=[
                                            {"label": "All", "value": "all"},
                                            {"label": "Automatic", "value": "automatic"},
                                            {"label": "Manual", "value": "manual"},
                                            {"label": "Other", "value": "other"},
                                        ],
                                        value="all",
                                    ),
                                    html.Label("Year Range"),
                                    dcc.RangeSlider(
                                        id="year-filter",
                                        min=year_min,
                                        max=year_max,
                                        step=1,
                                        value=[year_min, year_max],
                                        marks={year_min: str(year_min), year_max: str(year_max)},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    html.Label("Mileage Range"),
                                    dcc.RangeSlider(
                                        id="mileage-filter",
                                        min=mileage_min,
                                        max=mileage_max,
                                        step=5000,
                                        value=[mileage_min, mileage_max],
                                        marks={
                                            mileage_min: f"{mileage_min:,}",
                                            mileage_max: f"{mileage_max:,}",
                                        },
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="content",
                        children=[
                            dcc.Loading(
                                type="circle",
                                children=[
                                    html.Div(
                                        className="cards",
                                        children=[
                                            html.Div(
                                                className="card",
                                                children=[
                                                    html.H4("Listings Found"),
                                                    html.H2(id="listing-count"),
                                                ],
                                            ),
                                            html.Div(
                                                className="card",
                                                children=[
                                                    html.H4("Median Price"),
                                                    html.H2(id="median-price"),
                                                ],
                                            ),
                                            html.Div(
                                                className="card",
                                                children=[
                                                    html.H4("Median Mileage"),
                                                    html.H2(id="median-mileage"),
                                                ],
                                            ),
                                            html.Div(
                                                className="card",
                                                children=[
                                                    html.H4("Best Deal Score"),
                                                    html.H2(id="best-deal"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(id="price-mileage-scatter"),
                                    dcc.Graph(id="top-deals-bar"),
                                    dcc.Graph(id="price-boxplot"),
                                ],
                            ),
                            html.Div(
                                className="listing-detail-section",
                                children=[
                                    html.H3("Selected Listing Details"),
                                    html.P(
                                        "Click a point in the scatter plot or a bar in the "
                                        "Top 10 Deals chart to view details for that listing."
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        children=html.Div(id="selected-listing-details"),
                                    ),
                                ],
                            ),
                            html.Div(
                                className="table-section",
                                children=[
                                    html.Div(
                                        className="table-section-header",
                                        children=[
                                            html.H3("Top Matching Listings"),
                                            html.Button(
                                                "Export CSV",
                                                id="export-csv-button",
                                                className="export-button",
                                                n_clicks=0,
                                            ),
                                            dcc.Download(id="export-csv-download"),
                                        ],
                                    ),
                                    html.P(
                                        "The table below shows the best matching listings based "
                                        "on the current filters. Higher deal scores suggest that "
                                        "the vehicle is priced below comparable listings."
                                    ),
                                    dcc.Loading(
                                        type="circle",
                                        children=dash_table.DataTable(
                                            id="listing-table",
                                            columns=[
                                                {"name": "Vehicle", "id": "vehicle_label"},
                                                {
                                                    "name": "Price",
                                                    "id": "price",
                                                    "type": "numeric",
                                                    "format": {"specifier": "$,.0f"},
                                                },
                                                {
                                                    "name": "Market Median Price",
                                                    "id": "market_median_price",
                                                    "type": "numeric",
                                                    "format": {"specifier": "$,.0f"},
                                                },
                                                {
                                                    "name": "Mileage",
                                                    "id": "odometer",
                                                    "type": "numeric",
                                                    "format": {"specifier": ",.0f"},
                                                },
                                                {"name": "Condition", "id": "condition"},
                                                {"name": "Fuel", "id": "fuel"},
                                                {"name": "Transmission", "id": "transmission"},
                                                {"name": "State", "id": "state"},
                                                {
                                                    "name": "Deal Score",
                                                    "id": "deal_score",
                                                    "type": "numeric",
                                                    "format": {"specifier": "$,.0f"},
                                                },
                                            ],
                                            page_size=10,
                                            sort_action="native",
                                            filter_action="native",
                                            style_table={"overflowX": "auto"},
                                            style_cell={
                                                "textAlign": "left",
                                                "padding": "8px",
                                                "fontFamily": "Arial",
                                                "fontSize": "14px",
                                            },
                                            style_header={
                                                "fontWeight": "bold",
                                                "backgroundColor": "#f3f4f6",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {
                                                        "filter_query": "{deal_score} > 2000",
                                                        "column_id": "deal_score",
                                                    },
                                                    "backgroundColor": "#dcfce7",
                                                    "color": "#166534",
                                                    "fontWeight": "bold",
                                                },
                                                {
                                                    "if": {
                                                        "filter_query": "{deal_score} < 0",
                                                        "column_id": "deal_score",
                                                    },
                                                    "backgroundColor": "#fee2e2",
                                                    "color": "#991b1b",
                                                },
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
