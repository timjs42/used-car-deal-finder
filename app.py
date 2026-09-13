from dash import Dash

from callbacks import register_callbacks
from data import load_data
from layout import build_layout

df = load_data()

app = Dash(__name__)
server = app.server

app.layout = build_layout(df)
register_callbacks(app, df)

if __name__ == "__main__":
    app.run(debug=True)
