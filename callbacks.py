"""Callback registration for the Used Car Deal Finder app."""

from urllib.parse import parse_qs, urlencode, urlsplit

import pandas as pd
import plotly.express as px
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

TABLE_ROW_COLORS = {
    "light": {
        "positive_bg": "#dcfce7",
        "positive_text": "#166534",
        "negative_bg": "#fee2e2",
        "negative_text": "#991b1b",
    },
    "dark": {
        "positive_bg": "#103b2c",
        "positive_text": "#34d399",
        "negative_bg": "#3b1414",
        "negative_text": "#f87171",
    },
}

TABLE_BASE_STYLE = {
    "light": {"header_bg": "#f3f4f6", "header_text": "#14171c", "row_text": "#14171c"},
    "dark": {"header_bg": "#2b303a", "header_text": "#f1f0ec", "row_text": "#f1f0ec"},
}


def filter_listings(
    df,
    selected_manufacturer,
    model_search,
    selected_state,
    selected_conditions,
    selected_fuel,
    selected_transmission,
    selected_years,
    selected_mileage,
):
    """Apply the sidebar filters to df and return the matching rows."""
    filtered_df = df

    if selected_manufacturer:
        filtered_df = filtered_df[filtered_df["manufacturer"] == selected_manufacturer]

    if model_search:
        filtered_df = filtered_df[filtered_df["model"].str.contains(model_search.lower(), na=False)]

    if selected_state:
        filtered_df = filtered_df[filtered_df["state"] == selected_state]

    if selected_conditions:
        filtered_df = filtered_df[filtered_df["condition"].isin(selected_conditions)]

    if selected_fuel:
        filtered_df = filtered_df[filtered_df["fuel"] == selected_fuel]

    if selected_transmission != "all":
        filtered_df = filtered_df[filtered_df["transmission"] == selected_transmission]

    return filtered_df[
        (filtered_df["year"] >= selected_years[0])
        & (filtered_df["year"] <= selected_years[1])
        & (filtered_df["odometer"] >= selected_mileage[0])
        & (filtered_df["odometer"] <= selected_mileage[1])
    ]


def parse_filters_from_query(query_string, year_min, year_max, mileage_min, mileage_max):
    """Parse a URL query string into the filter values it represents.

    Out-of-range year/mileage bounds are clipped to the dataset's actual range so a
    stale or hand-edited link can't push the range sliders outside their min/max.
    """
    params = parse_qs(query_string or "")

    def first(key):
        values = params.get(key)
        return values[0] if values else None

    def parse_int(key, default):
        value = first(key)
        try:
            return int(value) if value is not None else default
        except ValueError:
            return default

    conditions = first("condition")

    return (
        first("manufacturer"),
        first("model"),
        first("state"),
        conditions.split(",") if conditions else [],
        first("fuel"),
        first("transmission") or "all",
        [
            max(year_min, min(year_max, parse_int("year_min", year_min))),
            max(year_min, min(year_max, parse_int("year_max", year_max))),
        ],
        [
            max(mileage_min, min(mileage_max, parse_int("mileage_min", mileage_min))),
            max(mileage_min, min(mileage_max, parse_int("mileage_max", mileage_max))),
        ],
    )


def build_query_from_filters(
    selected_manufacturer,
    model_search,
    selected_state,
    selected_conditions,
    selected_fuel,
    selected_transmission,
    selected_years,
    selected_mileage,
    year_min,
    year_max,
    mileage_min,
    mileage_max,
):
    """Build a shareable "?key=value" query string from the current filter values.

    Only filters that differ from their "no filter applied" default are included,
    so a view with few filters set gets a short, readable URL.
    """
    params = {}

    if selected_manufacturer:
        params["manufacturer"] = selected_manufacturer
    if model_search:
        params["model"] = model_search
    if selected_state:
        params["state"] = selected_state
    if selected_conditions:
        params["condition"] = ",".join(selected_conditions)
    if selected_fuel:
        params["fuel"] = selected_fuel
    if selected_transmission and selected_transmission != "all":
        params["transmission"] = selected_transmission
    if selected_years and tuple(selected_years) != (year_min, year_max):
        params["year_min"], params["year_max"] = selected_years
    if selected_mileage and tuple(selected_mileage) != (mileage_min, mileage_max):
        params["mileage_min"], params["mileage_max"] = selected_mileage

    query = urlencode(params)
    return f"?{query}" if query else ""


def register_callbacks(app, df: pd.DataFrame) -> None:
    """Attach all interactive callbacks to the given Dash app instance."""

    year_min = int(df["year"].min())
    year_max = int(df["year"].max())
    mileage_min = int(df["odometer"].min())
    mileage_max = int(df["odometer"].max())

    app.clientside_callback(
        """
        function(n_clicks) {
            if (!n_clicks) {
                return "";
            }
            navigator.clipboard.writeText(window.location.href);
            return "Link copied!";
        }
        """,
        Output("copy-link-feedback", "children"),
        Input("copy-link-button", "n_clicks"),
    )

    @app.callback(
        Output("manufacturer-filter", "value"),
        Output("model-search", "value"),
        Output("state-filter", "value"),
        Output("condition-filter", "value"),
        Output("fuel-filter", "value"),
        Output("transmission-filter", "value"),
        Output("year-filter", "value"),
        Output("mileage-filter", "value"),
        Output("url-synced", "data"),
        Input("url", "href"),
        State("url-synced", "data"),
    )
    def sync_filters_from_url(href, already_synced):
        if already_synced:
            raise PreventUpdate

        query = urlsplit(href).query if href else ""
        (
            manufacturer,
            model_search,
            state,
            conditions,
            fuel,
            transmission,
            year_range,
            mileage_range,
        ) = parse_filters_from_query(query, year_min, year_max, mileage_min, mileage_max)

        return (
            manufacturer,
            model_search,
            state,
            conditions,
            fuel,
            transmission,
            year_range,
            mileage_range,
            True,
        )

    @app.callback(
        Output("url", "search"),
        Input("manufacturer-filter", "value"),
        Input("model-search", "value"),
        Input("state-filter", "value"),
        Input("condition-filter", "value"),
        Input("fuel-filter", "value"),
        Input("transmission-filter", "value"),
        Input("year-filter", "value"),
        Input("mileage-filter", "value"),
    )
    def sync_url_from_filters(
        selected_manufacturer,
        model_search,
        selected_state,
        selected_conditions,
        selected_fuel,
        selected_transmission,
        selected_years,
        selected_mileage,
    ):
        return build_query_from_filters(
            selected_manufacturer,
            model_search,
            selected_state,
            selected_conditions,
            selected_fuel,
            selected_transmission,
            selected_years,
            selected_mileage,
            year_min,
            year_max,
            mileage_min,
            mileage_max,
        )

    app.clientside_callback(
        """
        function(n_clicks, currentTheme) {
            const theme = !n_clicks
                ? (currentTheme || "light")
                : (currentTheme === "dark" ? "light" : "dark");
            document.documentElement.setAttribute("data-theme", theme);
            const label = theme === "dark"
                ? "\\u2600\\ufe0f Light Mode"
                : "\\ud83c\\udf19 Dark Mode";
            return [theme, label];
        }
        """,
        Output("theme-store", "data"),
        Output("theme-toggle", "children"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
    )

    @app.callback(
        Output("sidebar-open", "data"),
        Output("filters-panel", "className"),
        Output("sidebar-toggle", "children"),
        Output("sidebar-toggle", "aria-expanded"),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-open", "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(_n_clicks, is_open):
        is_open = not is_open
        class_name = "filters-panel" if is_open else "filters-panel collapsed"
        label = "Hide Filters" if is_open else "Show Filters"
        return is_open, class_name, label, "true" if is_open else "false"

    @app.callback(
        Output("listing-count", "children"),
        Output("median-price", "children"),
        Output("median-mileage", "children"),
        Output("best-deal", "children"),
        Output("price-mileage-scatter", "figure"),
        Output("top-deals-bar", "figure"),
        Output("price-boxplot", "figure"),
        Output("listing-table", "data"),
        Output("listing-table", "style_header"),
        Output("listing-table", "style_cell"),
        Output("listing-table", "style_data_conditional"),
        Input("manufacturer-filter", "value"),
        Input("model-search", "value"),
        Input("state-filter", "value"),
        Input("condition-filter", "value"),
        Input("fuel-filter", "value"),
        Input("transmission-filter", "value"),
        Input("year-filter", "value"),
        Input("mileage-filter", "value"),
        Input("theme-store", "data"),
    )
    def update_dashboard(
        selected_manufacturer,
        model_search,
        selected_state,
        selected_conditions,
        selected_fuel,
        selected_transmission,
        selected_years,
        selected_mileage,
        theme,
    ):
        theme = theme if theme in TABLE_BASE_STYLE else "light"
        chart_template = "plotly_dark" if theme == "dark" else "plotly_white"
        row_colors = TABLE_ROW_COLORS[theme]
        base_style = TABLE_BASE_STYLE[theme]

        style_header = {
            "fontWeight": "bold",
            "backgroundColor": base_style["header_bg"],
            "color": base_style["header_text"],
        }
        style_cell = {
            "textAlign": "left",
            "padding": "8px",
            "fontFamily": "Arial",
            "fontSize": "14px",
            "backgroundColor": "transparent",
            "color": base_style["row_text"],
        }
        style_data_conditional = [
            {
                "if": {"filter_query": "{deal_score} > 2000", "column_id": "deal_score"},
                "backgroundColor": row_colors["positive_bg"],
                "color": row_colors["positive_text"],
                "fontWeight": "bold",
            },
            {
                "if": {"filter_query": "{deal_score} < 0", "column_id": "deal_score"},
                "backgroundColor": row_colors["negative_bg"],
                "color": row_colors["negative_text"],
            },
        ]

        filtered_df = filter_listings(
            df,
            selected_manufacturer,
            model_search,
            selected_state,
            selected_conditions,
            selected_fuel,
            selected_transmission,
            selected_years,
            selected_mileage,
        )

        if filtered_df.empty:
            empty_fig = px.scatter(title="No listings match the selected filters.")
            empty_fig.update_layout(template=chart_template)

            return (
                "0",
                "$0",
                "0 miles",
                "$0",
                empty_fig,
                empty_fig,
                empty_fig,
                [],
                style_header,
                style_cell,
                style_data_conditional,
            )

        listing_count = f"{len(filtered_df):,}"
        median_price = f"${filtered_df['price'].median():,.0f}"
        median_mileage = f"{filtered_df['odometer'].median():,.0f} miles"
        best_deal = f"${filtered_df['deal_score'].max():,.0f}"

        # Chart 1: price vs. mileage scatter plot
        scatter_fig = px.scatter(
            filtered_df,
            x="odometer",
            y="price",
            color="year",
            custom_data=["listing_id"],
            hover_data=[
                "vehicle_label",
                "condition",
                "fuel",
                "transmission",
                "state",
                "deal_score",
            ],
            title="Price vs. Mileage",
            labels={
                "odometer": "Mileage",
                "price": "Listing Price",
                "year": "Model Year",
                "deal_score": "Deal Score",
                "vehicle_label": "Vehicle",
            },
        )
        scatter_fig.update_layout(
            xaxis_tickformat=",",
            yaxis_tickprefix="$",
            template=chart_template,
            margin=dict(l=40, r=40, t=70, b=40),
        )

        # Chart 2: top 10 deals bar chart
        top_deals = filtered_df.sort_values("deal_score", ascending=False).head(10).copy()

        bar_fig = px.bar(
            top_deals,
            x="deal_score",
            y="vehicle_label",
            orientation="h",
            color="deal_score",
            custom_data=["listing_id"],
            title="Top 10 Potential Best Deals",
            labels={
                "deal_score": "Estimated Savings Compared with Similar Vehicles",
                "vehicle_label": "Vehicle",
            },
            hover_data=["price", "market_median_price", "odometer", "condition", "state"],
        )
        bar_fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickprefix="$",
            template=chart_template,
            showlegend=False,
            margin=dict(l=40, r=40, t=70, b=40),
        )

        # Chart 3: price distribution box plot
        if "condition" in filtered_df.columns and filtered_df["condition"].nunique() > 1:
            box_fig = px.box(
                filtered_df,
                x="condition",
                y="price",
                color="condition",
                title="Price Distribution by Vehicle Condition",
                labels={"condition": "Condition", "price": "Listing Price"},
            )
        else:
            box_fig = px.box(
                filtered_df,
                x="manufacturer",
                y="price",
                title="Price Distribution by Manufacturer",
                labels={"manufacturer": "Manufacturer", "price": "Listing Price"},
            )

        box_fig.update_layout(
            yaxis_tickprefix="$",
            template=chart_template,
            showlegend=False,
            margin=dict(l=40, r=40, t=70, b=40),
        )

        # Data table
        table_columns = [
            "vehicle_label",
            "price",
            "market_median_price",
            "odometer",
            "condition",
            "fuel",
            "transmission",
            "state",
            "deal_score",
        ]
        table_data = (
            filtered_df.sort_values("deal_score", ascending=False)
            .head(50)[table_columns]
            .to_dict("records")
        )

        return (
            listing_count,
            median_price,
            median_mileage,
            best_deal,
            scatter_fig,
            bar_fig,
            box_fig,
            table_data,
            style_header,
            style_cell,
            style_data_conditional,
        )

    @app.callback(
        Output("export-csv-download", "data"),
        Input("export-csv-button", "n_clicks"),
        State("manufacturer-filter", "value"),
        State("model-search", "value"),
        State("state-filter", "value"),
        State("condition-filter", "value"),
        State("fuel-filter", "value"),
        State("transmission-filter", "value"),
        State("year-filter", "value"),
        State("mileage-filter", "value"),
        prevent_initial_call=True,
    )
    def export_csv(
        _n_clicks,
        selected_manufacturer,
        model_search,
        selected_state,
        selected_conditions,
        selected_fuel,
        selected_transmission,
        selected_years,
        selected_mileage,
    ):
        filtered_df = filter_listings(
            df,
            selected_manufacturer,
            model_search,
            selected_state,
            selected_conditions,
            selected_fuel,
            selected_transmission,
            selected_years,
            selected_mileage,
        )
        return dcc.send_data_frame(
            filtered_df.sort_values("deal_score", ascending=False).to_csv,
            "used_car_deals.csv",
            index=False,
        )

    @app.callback(
        Output("selected-listing-details", "children"),
        Input("price-mileage-scatter", "clickData"),
        Input("top-deals-bar", "clickData"),
    )
    def display_selected_listing(scatter_click, bar_click):
        click_data = scatter_click or bar_click

        if click_data is None:
            return html.Div(
                className="empty-listing-message",
                children="No listing selected yet. Click a chart point or bar to see details.",
            )

        listing_id = click_data["points"][0]["customdata"][0]
        selected = df[df["listing_id"] == listing_id]

        if selected.empty:
            return html.Div("Listing details could not be found.")

        row = selected.iloc[0]

        vehicle_label = row.get("vehicle_label", "Unknown Vehicle")
        price = row.get("price", 0)
        market_median_price = row.get("market_median_price", 0)
        deal_score = row.get("deal_score", 0)
        odometer = row.get("odometer", 0)

        detail_items = [
            html.H4(vehicle_label),
            html.Div(
                className="detail-grid",
                children=[
                    html.Div([html.Strong("Price"), html.P(f"${price:,.0f}")]),
                    html.Div(
                        [
                            html.Strong("Market Median Price"),
                            html.P(f"${market_median_price:,.0f}"),
                        ]
                    ),
                    html.Div([html.Strong("Deal Score"), html.P(f"${deal_score:,.0f}")]),
                    html.Div([html.Strong("Mileage"), html.P(f"{odometer:,.0f} miles")]),
                    html.Div(
                        [
                            html.Strong("Condition"),
                            html.P(str(row.get("condition", "Unknown")).title()),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("Fuel"),
                            html.P(str(row.get("fuel", "Unknown")).title()),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("Transmission"),
                            html.P(str(row.get("transmission", "Unknown")).title()),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("State"),
                            html.P(str(row.get("state", "Unknown")).upper()),
                        ]
                    ),
                ],
            ),
        ]

        if "region" in row and pd.notna(row["region"]):
            detail_items.append(html.P(f"Region: {str(row['region']).title()}"))

        if "posting_date" in row and pd.notna(row["posting_date"]):
            detail_items.append(html.P(f"Posting Date: {row['posting_date']}"))

        if "description" in row and pd.notna(row["description"]):
            description = str(row["description"])
            description_preview = (
                description[:500] + "..." if len(description) > 500 else description
            )
            detail_items.append(html.H5("Listing Description"))
            detail_items.append(html.P(description_preview, className="listing-description"))

        if "url" in row and pd.notna(row["url"]):
            detail_items.append(
                html.A(
                    "Open Original Listing",
                    href=row["url"],
                    target="_blank",
                    className="listing-link",
                )
            )

        return html.Div(className="listing-detail-card", children=detail_items)
