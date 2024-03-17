import dash
from spitec import *

local_file = Path("data/2024-01-22.h5")
site_coords = get_sites_coords(local_file)
site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

station_map = create_station_map(site_array, lat_array, lon_array)
station_data  = create_station_data()
app.layout = create_layout(station_map, station_data)

register_callbacks(app, station_map, station_data)

if __name__ == "__main__":
    app.run_server(debug=True)