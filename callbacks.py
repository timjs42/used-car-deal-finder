"""Callback registration for the Used Car Deal Finder app."""

import pandas as pd
import plotly.express as px
from dash import Input, Output, html


def register_callbacks(app, df: pd.DataFrame) -> None:
    """Attach all interactive callbacks to the given Dash app instance."""

    @app.callback(
        Output("listing-count", "children"),
        Output("median-price", "children"),
        Output("median-mileage", "children"),
        Output("best-deal", "children"),
        Output("price-mileage-scatter", "figure"),
        Output("top-deals-bar", "figure"),
        Output("price-boxplot", "figure"),
        Output("listing-table", "data"),
        Input("manufacturer-filter", "value"),
        Input("model-search", "value"),
        Input("state-filter", "value"),
        Input("condition-filter", "value"),
        Input("fuel-filter", "value"),
        Input("transmission-filter", "value"),
        Input("year-filter", "value"),
        Input("mileage-filter", "value"),
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
    ):
        filtered_df = df.copy()

        if selected_manufacturer:
            filtered_df = filtered_df[filtered_df["manufacturer"] == selected_manufacturer]

        if model_search:
            filtered_df = filtered_df[
                filtered_df["model"].str.contains(model_search.lower(), na=False)
            ]

        if selected_state:
            filtered_df = filtered_df[filtered_df["state"] == selected_state]

        if selected_conditions:
            filtered_df = filtered_df[filtered_df["condition"].isin(selected_conditions)]

        if selected_fuel:
            filtered_df = filtered_df[filtered_df["fuel"] == selected_fuel]

        if selected_transmission != "all":
            filtered_df = filtered_df[filtered_df["transmission"] == selected_transmission]

        filtered_df = filtered_df[
            (filtered_df["year"] >= selected_years[0])
            & (filtered_df["year"] <= selected_years[1])
            & (filtered_df["odometer"] >= selected_mileage[0])
            & (filtered_df["odometer"] <= selected_mileage[1])
        ]

        if filtered_df.empty:
            empty_fig = px.scatter(title="No listings match the selected filters.")
            empty_fig.update_layout(template="plotly_white")

            return (
                "0",
                "$0",
                "0 miles",
                "$0",
                empty_fig,
                empty_fig,
                empty_fig,
                [],
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
            template="plotly_white",
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
            template="plotly_white",
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
            template="plotly_white",
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
