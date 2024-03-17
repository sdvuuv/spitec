from dash.dependencies import Input, Output


def register_callbacks(app, station_map, station_data):
    @app.callback(
        Output("graph-station-map", "figure"),
        [Input("projection-radio", "value")]
    )
    def update_map_projection(projection_value):
        station_map.update_layout(
            geo=dict(projection_type=projection_value)
        )
        return station_map

