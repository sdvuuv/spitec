from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from ..view import PointColor, ProjectionType, languages
from ..processing import *
from datetime import datetime, UTC
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from pathlib import Path
from numpy.typing import NDArray
import numpy as np


language = languages["en"]
FILE_FOLDER = Path("data")
site_coords = None


def register_callbacks(
    app: dash.Dash,
    site_map: go.Figure,
    site_data: go.Figure,
    projection_radio: dbc.RadioItems,
    time_slider: dcc.RangeSlider,
    checkbox_site: dbc.Checkbox,
) -> None:

    @app.callback(
        Output("graph-site-map", "figure", allow_duplicate=True),
        [Input("projection-radio", "value")],
        prevent_initial_call=True,
    )
    def update_map_projection(projection_value: ProjectionType) -> go.Figure:
        if projection_value != site_map.layout.geo.projection.type:
            site_map.update_layout(
                geo=dict(projection_type=projection_value)
            )
        projection_radio.value = projection_value
        return site_map

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-map", "clickData"),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
        ],
        [Input("graph-site-map", "clickData")],
        [
            State("site-names-store", "data"),
            State("local-file-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_site_data(
        clickData: dict[str, list[dict[str, float | str | dict]]],
        data: NDArray,
        local_file: str,
    ) -> list[go.Figure | None | bool | dcc.RangeSlider]:
        shift = -0.5

        if clickData is not None:
            site_name = clickData["points"][0]["text"].lower()
            site_idx = clickData["points"][0]["pointIndex"]
            site_color = site_map.data[0].marker.color[site_idx]
            if (
                site_color == PointColor.SILVER.value
                or site_color == PointColor.GREEN.value
            ):
                add_line(shift, site_name, site_idx, local_file)
            elif site_color == PointColor.RED.value:
                delete_line(shift, site_name, site_idx, data)
        time_slider.disabled = True if len(site_data.data) == 0 else False
        return site_map, None, site_data, time_slider

    def add_line(
        shift: float, site_name: Site, site_idx: int, local_file: str
    ) -> None:
        colors = site_map.data[0].marker.color.copy()
        colors[site_idx] = PointColor.RED.value
        site_map.data[0].marker.color = colors

        site_data_tmp = retrieve_data(local_file, [site_name])
        sat = list(site_data_tmp[site_name].keys())[0]
        dataproduct = DataProducts.dtec_2_10

        vals = site_data_tmp[site_name][sat][dataproduct]
        times = site_data_tmp[site_name][sat][DataProducts.time]

        number_lines = len(site_data.data)

        site_data.add_trace(
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
        y_tickmode = site_data.layout.yaxis.tickmode
        if y_tickmode is None:
            site_data.layout.yaxis.tickmode = "array"
            site_data.layout.yaxis.tickvals = [shift * number_lines]
            site_data.layout.yaxis.ticktext = [site_name.upper()]
        else:
            yaxis_data = {"tickvals": [], "ticktext": []}
            for i, site in enumerate(site_data.layout.yaxis.ticktext):
                yaxis_data["tickvals"].append(
                    site_data.layout.yaxis.tickvals[i]
                )
                yaxis_data["ticktext"].append(site)
            yaxis_data["tickvals"].append(shift * number_lines)
            yaxis_data["ticktext"].append(site_name.upper())
            update_yaxis(yaxis_data)

    def delete_line(
        shift: float, site_name: Site, site_idx: int, data: NDArray
    ) -> None:
        colors = site_map.data[0].marker.color.copy()
        if data is not None and site_name in data:
            colors[site_idx] = PointColor.GREEN.value
        else:
            colors[site_idx] = PointColor.SILVER.value
        site_map.data[0].marker.color = colors

        site_data_tmp = dict()
        for i, site in enumerate(site_data.data):
            if site.name.lower() != site_name:
                site_data_tmp[site.name] = dict()
                site_data_tmp[site.name]["x"] = site.x
                site_data_tmp[site.name]["y"] = site.y - shift * i
        site_data.data = []
        for i, site in enumerate(list(site_data_tmp.keys())):
            site_data.add_trace(
                go.Scatter(
                    x=site_data_tmp[site]["x"],
                    y=site_data_tmp[site]["y"] + shift * i,
                    mode="lines",
                    name=site,
                )
            )
        delete_value_yaxis(shift, site_name)

    def delete_value_yaxis(shift: float, site_name: Site) -> None:
        yaxis_data = {"tickvals": [], "ticktext": []}
        for i, site in enumerate(site_data.layout.yaxis.ticktext):
            if site.lower() != site_name:
                yaxis_data["ticktext"].append(site)
        for i in range(len(yaxis_data["ticktext"])):
            yaxis_data["tickvals"].append(shift * i)
        update_yaxis(yaxis_data)

    def update_yaxis(yaxis_data: dict[str, list[float | str]]) -> None:
        site_data.update_layout(
            yaxis=dict(
                tickmode="array",
                tickvals=yaxis_data["tickvals"],
                ticktext=yaxis_data["ticktext"],
            )
        )

    @app.callback(
        [
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
        ],
        [Input("time-slider", "value")],
        prevent_initial_call=True,
    )
    def change_xaxis(value: list[int]) -> list[go.Figure | dcc.RangeSlider]:
        if len(site_data.data) == 0:
            return site_data, time_slider
        date = site_data.data[0].x[0]

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
        site_data.update_layout(xaxis=dict(range=[start_limit, end_limit]))
        return site_data, time_slider

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
        ],
        [Input("clear-all", "n_clicks")],
        [State("site-names-store", "data")],
        prevent_initial_call=True,
    )
    def clear_all(n: int, data: NDArray) -> list[go.Figure | dcc.RangeSlider]:
        if site_map.data[0].marker.color is None:
            return site_map, site_data, time_slider
        colors = site_map.data[0].marker.color.copy()
        for i, color in enumerate(colors):
            if color == PointColor.RED.value:
                if (
                    data is not None
                    and site_map.data[0].text[i].lower() in data
                ):
                    colors[i] = PointColor.GREEN.value
                else:
                    colors[i] = PointColor.SILVER.value
        site_map.data[0].marker.color = colors
        clear_all_graphs()
        return site_map, site_data, time_slider

    def clear_all_graphs() -> None:
        site_data.data = []
        site_data.layout.xaxis = dict(title="Время")
        site_data.layout.yaxis = dict()

        time_slider.value = [0, 24]
        time_slider.disabled = True

    @app.callback(
        Output("graph-site-map", "figure", allow_duplicate=True),
        [Input("hide-show-site", "value")],
        prevent_initial_call=True,
    )
    def hide_show_site(value: bool) -> go.Figure:
        if value:
            site_map.data[0].mode = "markers+text"
        else:
            site_map.data[0].mode = "markers"
        checkbox_site.value = value
        return site_map

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("min-lat", "invalid"),
            Output("max-lat", "invalid"),
            Output("min-lon", "invalid"),
            Output("max-lon", "invalid"),
            Output("site-names-store", "data", allow_duplicate=True),
        ],
        [Input("apply-lat-lon", "n_clicks")],
        [
            State("min-lat", "value"),
            State("max-lat", "value"),
            State("min-lon", "value"),
            State("max-lon", "value"),
            State("site-names-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def apply_selection_by_region(
        n: int,
        min_lat: int,
        max_lat: int,
        min_lon: int,
        max_lon: int,
        data: list[str],
    ) -> list[go.Figure | bool | list[str]]:
        return_value_list = [site_map, False, False, False, False, data]

        check_value(min_lat, 1, return_value_list)
        check_value(max_lat, 2, return_value_list)
        check_value(min_lon, 3, return_value_list)
        check_value(max_lon, 4, return_value_list)

        if True in return_value_list or site_coords is None:
            return return_value_list
        else:
            sites_by_region = select_sites_by_region(
                site_coords, min_lat, max_lat, min_lon, max_lon
            )
            change_points_on_map(return_value_list, sites_by_region)
        return_value_list[0] = site_map
        return return_value_list

    def change_points_on_map(
        return_value_list: list[go.Figure | bool | list[str]],
        sites_by_region: dict[Site, dict[Coordinate, float]],
    ) -> None:
        sites, _, _ = get_namelatlon_arrays(sites_by_region)
        return_value_list[-1] = sites

        colors = site_map.data[0].marker.color.copy()
        for i, site in enumerate(site_map.data[0].text):
            if site.lower() in sites:
                if colors[i] == PointColor.SILVER.value:
                    colors[i] = PointColor.GREEN.value
            elif colors[i] == PointColor.GREEN.value:
                colors[i] = PointColor.SILVER.value
        site_map.data[0].marker.color = colors

    def check_value(
        degrees: int,
        idx: int,
        return_value_list: dict[str, go.Figure | bool],
    ) -> None:
        if degrees is None:
            return_value_list[idx] = True

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("distance", "invalid"),
            Output("center-point-lat", "invalid"),
            Output("center-point-lon", "invalid"),
            Output("site-names-store", "data", allow_duplicate=True),
        ],
        [Input("apply-great-circle-distance", "n_clicks")],
        [
            State("distance", "value"),
            State("center-point-lat", "value"),
            State("center-point-lon", "value"),
            State("site-names-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def apply_great_circle_distance(
        n: int,
        distance: int,
        lat: int,
        lon: int,
        data: list[str],
    ) -> list[go.Figure | bool | list[str]]:
        return_value_list = [site_map, False, False, False, data]

        check_value(distance, 1, return_value_list)
        check_value(lat, 2, return_value_list)
        check_value(lon, 3, return_value_list)

        if True in return_value_list or site_coords is None:
            return return_value_list
        else:
            central_point = dict()
            central_point[Coordinate.lat] = lat
            central_point[Coordinate.lon] = lon
            sites_by_region = select_sites_in_circle(
                site_coords, central_point, distance
            )
            change_points_on_map(return_value_list, sites_by_region)
        return return_value_list

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("site-names-store", "data", allow_duplicate=True),
        ],
        [
            Input("clear-selection-by-region1", "n_clicks"),
            Input("clear-selection-by-region2", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def clear_selection_by_region(n1: int, n2: int) -> list[go.Figure | None]:
        if site_map.data[0].marker.color is not None:
            colors = site_map.data[0].marker.color.copy()
            for i, color in enumerate(colors):
                if color == PointColor.GREEN.value:
                    colors[i] = PointColor.SILVER.value
            site_map.data[0].marker.color = colors
        return site_map, None

    @app.callback(
        [
            Output("download-window", "is_open"),
            Output("downloaded", "style", allow_duplicate=True),
            Output("downloaded", "children", allow_duplicate=True),
        ],
        [Input("download", "n_clicks")],
        [State("download-window", "is_open")],
        prevent_initial_call=True,
    )
    def open_close_download_window(
        n1: int, is_open: bool
    ) -> list[bool | dict[str, str] | str]:
        style = {"visibility": "hidden"}
        return not is_open, style, ""

    @app.callback(
        [
            Output("downloaded", "style", allow_duplicate=True),
            Output("downloaded", "children", allow_duplicate=True),
        ],
        [Input("download-file", "n_clicks")],
        [State("date-selection", "date")],
        prevent_initial_call=True,
    )
    def download_file(n1: int, date: str) -> dict[str, str]:
        text = language["download_window"]["successаfuly"]
        color = "green"
        if date is None:
            text = language["download_window"]["unsuccessаfuly"]
        else:
            if not FILE_FOLDER.exists():
                FILE_FOLDER.mkdir()
            local_file = FILE_FOLDER / (date + ".h5")
            if local_file.exists():
                text = language["download_window"]["repeat-action"]
            else:
                local_file.touch()
                if not load_data(date, local_file):
                    text = language["download_window"]["error"]
                    local_file.unlink()
        if text != language["download_window"]["successаfuly"]:
            color = "red"
        style = {
            "text-align": "center",
            "margin-top": "20px",
            "color": color,
        }
        return style, text

    @app.callback(
        [
            Output("open-window", "is_open", allow_duplicate=True),
            Output("select-file", "options"),
        ],
        [Input("open", "n_clicks")],
        [State("open-window", "is_open")],
        prevent_initial_call=True,
    )
    def open_close_open_window(
        n1: int, is_open: bool
    ) -> list[bool | list[dict[str, str]]]:
        options = []
        if FILE_FOLDER.exists():
            for file_path in FILE_FOLDER.iterdir():
                if file_path.is_file():
                    options.append(
                        {"label": file_path.name, "value": file_path.name}
                    )
        return not is_open, options

    @app.callback(
        [
            Output("open-window", "is_open"),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("local-file-store", "data"),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("div-time-slider", "children", allow_duplicate=True),
            Output("site-names-store", "data"),
        ],
        [Input("open-file", "n_clicks")],
        [State("select-file", "value")],
        prevent_initial_call=True,
    )
    def open_close_open_window(
        n1: int, value: str
    ) -> list[bool | go.Figure | str | dcc.RangeSlider | None]:
        global site_coords
        local_file = FILE_FOLDER / value
        site_coords = get_sites_coords(local_file)
        site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

        colors = np.array([PointColor.SILVER.value] * site_array.shape[0])

        site_map.data[0].lat = lat_array
        site_map.data[0].lon = lon_array
        site_map.data[0].text = [site.upper() for site in site_array]
        site_map.data[0].marker.color = colors

        clear_all_graphs()

        return (
            False,
            site_map,
            str(local_file),
            site_data,
            time_slider,
            None,
        )
