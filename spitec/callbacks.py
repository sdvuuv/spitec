from dash.dependencies import Input, Output
import plotly.graph_objects as go
from .visualization import PointColor, ProjectionType
from .data_processing import Sat, retrieve_data
from .data_products import DataProduct, DataProducts


def register_callbacks(app, station_map, station_data, LOCAL_FILE) -> None:
    @app.callback(
        Output("graph-station-map", "figure", allow_duplicate=True),
        [Input("projection-radio", "value")],
        prevent_initial_call=True,
    )
    def update_map_projection(projection_value: ProjectionType) -> go.Figure:
        if projection_value != station_map.layout.geo.projection.type:
            station_map.update_layout(geo=dict(projection_type=projection_value))
        return station_map

    @app.callback(
        [
            Output("graph-station-map", "figure"),
            Output("graph-station-map", "clickData"),
            Output("graph-station-data", "figure"),
        ],
        [Input("graph-station-map", "clickData")],
    )
    def update_station_data(
        clickData: dict[str, list[dict[str, float | str | dict]]]
    ) -> list[go.Figure | None]:
        shift = 0.5

        if clickData is not None:
            site_name = clickData["points"][0]["text"].lower()
            site_idx = clickData["points"][0]["pointIndex"]
            site_color = station_map.data[0].marker.color[site_idx]
            if site_color == PointColor.SILVER.value:
                station_map.data[0].marker.color[site_idx] = PointColor.RED.value

                site_data = retrieve_data(LOCAL_FILE, [site_name])
                sat = list(site_data[site_name].keys())[0]
                dataproduct = DataProducts.dtec_2_10

                vals = site_data[site_name][sat][dataproduct]
                times = site_data[site_name][sat][DataProducts.time]

                number_lines = len(station_data.data)

                station_data.add_trace(
                    go.Scatter(
                        x=times,
                        y=vals + shift * number_lines,
                        mode="lines",
                        name=site_name.upper(),
                    )
                )
            elif site_color == PointColor.RED.value:
                station_map.data[0].marker.color[site_idx] = PointColor.SILVER.value

                site_data = dict()
                for i, site in enumerate(station_data.data):
                    if site.name.lower() != site_name:
                        site_data[site.name] = dict()
                        site_data[site.name]["x"] = site.x
                        site_data[site.name]["y"] = site.y - shift * i
                station_data.data = []
                for i, site in enumerate(list(site_data.keys())):
                    station_data.add_trace(
                        go.Scatter(
                            x=site_data[site]["x"],
                            y=site_data[site]["y"] + shift * i,
                            mode="lines",
                            name=site,
                        )
                    )
        return station_map, None, station_data
