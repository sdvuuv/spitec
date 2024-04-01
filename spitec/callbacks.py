from dash.dependencies import Input, Output
import plotly.graph_objects as go
from .visualization import PointColor, ProjectionType
from .data_processing import Sat, retrieve_data
from .data_products import DataProduct, DataProducts
from .station_processing import Site
from datetime import datetime, UTC
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from pathlib import Path


def register_callbacks(
    app: dash.Dash,
    LOCAL_FILE: Path | str,
    station_map: go.Figure,
    station_data: go.Figure,
    projection_radio: dbc.RadioItems,
    time_slider: dcc.RangeSlider,
    checkbox_site: dbc.Checkbox,
) -> None:
    @app.callback(
        Output("graph-station-map", "figure", allow_duplicate=True),
        [Input("projection-radio", "value")],
        prevent_initial_call=True,
    )
    def update_map_projection(projection_value: ProjectionType) -> go.Figure:
        if projection_value != station_map.layout.geo.projection.type:
            station_map.update_layout(
                geo=dict(projection_type=projection_value)
            )
        projection_radio.value = projection_value
        return station_map

    @app.callback(
        [
            Output("graph-station-map", "figure", allow_duplicate=True),
            Output("graph-station-map", "clickData"),
            Output("graph-station-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
        ],
        [Input("graph-station-map", "clickData")],
        prevent_initial_call=True,
    )
    def update_station_data(
        clickData: dict[str, list[dict[str, float | str | dict]]]
    ) -> list[go.Figure | None | bool]:
        shift = -0.5

        if clickData is not None:
            site_name = clickData["points"][0]["text"].lower()
            site_idx = clickData["points"][0]["pointIndex"]
            site_color = station_map.data[0].marker.color[site_idx]
            if site_color == PointColor.SILVER.value:
                add_line(shift, site_name, site_idx)
            elif site_color == PointColor.RED.value:
                delete_line(shift, site_name, site_idx)
        time_slider.disabled = True if len(station_data.data) == 0 else False
        return station_map, None, station_data, time_slider

    def add_line(shift: float, site_name: Site, site_idx: int) -> None:
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

        add_value_yaxis(shift, site_name, number_lines)

    def add_value_yaxis(
        shift: float, site_name: Site, number_lines: int
    ) -> None:
        y_tickmode = station_data.layout.yaxis.tickmode
        if y_tickmode is None:
            station_data.layout.yaxis.tickmode = "array"
            station_data.layout.yaxis.tickvals = [shift * number_lines]
            station_data.layout.yaxis.ticktext = [site_name.upper()]
        else:
            yaxis_data = {"tickvals": [], "ticktext": []}
            for i, site in enumerate(station_data.layout.yaxis.ticktext):
                yaxis_data["tickvals"].append(
                    station_data.layout.yaxis.tickvals[i]
                )
                yaxis_data["ticktext"].append(site)
            yaxis_data["tickvals"].append(shift * number_lines)
            yaxis_data["ticktext"].append(site_name.upper())
            update_yaxis(yaxis_data)

    def delete_line(shift: float, site_name: Site, site_idx: int) -> None:
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
        delete_value_yaxis(shift, site_name)

    def delete_value_yaxis(shift: float, site_name: Site) -> None:
        yaxis_data = {"tickvals": [], "ticktext": []}
        for i, site in enumerate(station_data.layout.yaxis.ticktext):
            if site.lower() != site_name:
                yaxis_data["ticktext"].append(site)
        for i in range(len(yaxis_data["ticktext"])):
            yaxis_data["tickvals"].append(shift * i)
        update_yaxis(yaxis_data)

    def update_yaxis(yaxis_data: dict[str, list[float | str]]) -> None:
        station_data.update_layout(
            yaxis=dict(
                tickmode="array",
                tickvals=yaxis_data["tickvals"],
                ticktext=yaxis_data["ticktext"],
            )
        )

    @app.callback(
        [
            Output("graph-station-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
        ],
        [Input("time-slider", "value")],
        prevent_initial_call=True,
    )
    def change_xaxis(value: list[int]) -> list[go.Figure | bool]:
        if len(station_data.data) == 0:
            return station_data, time_slider
        date = station_data.data[0].x[0]

        hour_start_limit = 23 if value[0] == 24 else value[0]
        minute_start_limit = 59 if value[0] == 24 else 0
        second_start_limit = 59 if value[0] == 24 else 0

        hour_end_limit = 23 if value[1] == 24 else value[1]
        minute_end_limit = 59 if value[1] == 24 else 0
        second_end_limit = 59 if value[1] == 24 else 0

        start_limit = datetime(
            date.year,
            date.month,
            date.day,
            hour=hour_start_limit,
            minute=minute_start_limit,
            second=second_start_limit,
            tzinfo=UTC,
        )
        end_limit = datetime(
            date.year,
            date.month,
            date.day,
            hour=hour_end_limit,
            minute=minute_end_limit,
            second=second_end_limit,
            tzinfo=UTC,
        )

        time_slider.value = [value[0], value[1]]
        station_data.update_layout(xaxis=dict(range=[start_limit, end_limit]))
        return station_data, time_slider

    @app.callback(
        [
            Output("graph-station-map", "figure", allow_duplicate=True),
            Output("graph-station-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
        ],
        [Input("clear-all", "n_clicks")],
        prevent_initial_call=True,
    )
    def clear_all(n_clicks: int) -> list[go.Figure | list[int]]:
        for i, color in enumerate(station_map.data[0].marker.color):
            if color == PointColor.RED.value:
                station_map.data[0].marker.color[i] = PointColor.SILVER.value
        station_data.data = []
        station_data.layout.xaxis = dict(title="Время")
        station_data.layout.yaxis = dict()

        time_slider.value = [0, 24]
        time_slider.disabled = True
        return station_map, station_data, time_slider

    @app.callback(
        Output("graph-station-map", "figure", allow_duplicate=True),
        [Input("hide-show-site", "value")],
        prevent_initial_call=True,
    )
    def hide_show_site(value: bool) -> go.Figure:
        if value:
            station_map.data[0].mode = "markers+text"
        else:
            station_map.data[0].mode = "markers"
        checkbox_site.value = value
        return station_map
