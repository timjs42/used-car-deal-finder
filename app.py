from dash import Dash

from callbacks import register_callbacks
from data import load_data
from layout import build_layout

df = load_data()

app = Dash(__name__, title="Used Car Deal Finder")
server = app.server

app.index_string = """<!DOCTYPE html>
<html lang="en">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

app.layout = build_layout(df)
register_callbacks(app, df)

if __name__ == "__main__":
    app.run(debug=True)
