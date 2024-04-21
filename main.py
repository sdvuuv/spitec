import dash
from spitec import *

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = create_layout()

register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
