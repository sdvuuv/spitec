import dash
from spitec import *

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

site_map = create_site_map()
site_data = create_site_data()

projection_radio = create_projection_radio()
time_slider = create_time_slider()
checkbox_site = create_checkbox_site()
selection_data_types = create_selection_data_types()

app.layout = create_layout(
    site_map,
    site_data,
    projection_radio,
    time_slider,
    checkbox_site,
    selection_data_types,
)

register_callbacks(
    app,
    site_map,
    site_data,
    projection_radio,
    time_slider,
    checkbox_site,
    selection_data_types,
)

if __name__ == "__main__":
    app.run_server(host='0.0.0.0')
