# Used Car Deal Finder

**[Live demo](https://used-car-deal-finder.onrender.com/)** — hosted on Render's free tier. If it's been quiet for a while, the first load can take 30-60 seconds to spin back up.

[![CI](https://github.com/timjs42/used-car-deal-finder/actions/workflows/ci.yml/badge.svg)](https://github.com/timjs42/used-car-deal-finder/actions/workflows/ci.yml)

An interactive Dash dashboard for exploring used car listings and surfacing potential deals — vehicles priced below what comparable listings (same manufacturer, model, and year) are going for.

## Features

- **Filtering** by manufacturer, model keyword, state, condition, fuel type, transmission, year range, and mileage range
- **Deal score** for every listing: `market median price − listing price`. A positive score means the car is priced below what similar vehicles are selling for.
- **Interactive charts**: price vs. mileage scatter plot, top 10 potential deals, and price distribution by condition
- **Click-to-inspect**: click any point or bar to pull up full listing details, including description and a link to the original posting
- **Sortable/filterable results table** with conditional formatting highlighting strong and weak deals

## Tech stack

- **Frontend/backend**: [Dash](https://dash.plotly.com/) (Python), Plotly
- **Data**: pandas
- **Testing**: pytest, run automatically on every push via GitHub Actions
- **Deployment**: Render (gunicorn)

## Project structure

```
used-car-deal-finder/
├── app.py                   # entry point — wires data, layout, and callbacks together
├── data.py                  # load_data(): cleaning and deal-score calculation
├── layout.py                # build_layout(): filter sidebar, charts, table
├── callbacks.py             # register_callbacks(): filtering and click-to-inspect logic
├── data_pipeline/
│   ├── clean_data.py        # raw Kaggle data -> cleaned CSV
│   └── make_sample.py       # cleaned CSV -> stratified, size-reduced sample
├── data/
│   └── used_cars_sample.csv # ~8,000-row sample used by the live app
├── tests/
│   └── test_data.py         # pytest coverage for load_data()
├── assets/
│   └── style.css
└── .github/workflows/ci.yml # runs pytest on every push/PR
```

## How deal score works

For each listing, `market_median_price` is the median price of all listings with the same manufacturer, model, and year. `deal_score` is `market_median_price - price`. A deal score of `+2,000` means the car is listed $2,000 below what comparable vehicles are going for; a negative score means it's priced above the going rate.

## Data

The sample dataset (`data/used_cars_sample.csv`) is a stratified sample of a larger cleaned used-car listings dataset, sampled proportionally by manufacturer so smaller/rarer manufacturers aren't dropped. Listing descriptions are truncated to 300 characters in the sample to keep the file size manageable for the repo.

To regenerate the sample from a full raw dataset:

```bash
python data_pipeline/clean_data.py
python data_pipeline/make_sample.py
```

## Running locally

```bash
git clone https://github.com/timjs42/used-car-deal-finder.git
cd used-car-deal-finder
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:8050/` in your browser.

## Running tests

```bash
python -m pytest tests/ -v
```