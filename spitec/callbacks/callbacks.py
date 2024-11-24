from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from spitec.view.visualization import *
from spitec.view.languages import languages
from spitec.processing.data_processing import *
from spitec.processing.data_products import DataProducts
from spitec.processing.trajectorie import Trajectorie
from spitec.processing.site_processing import *
from spitec.callbacks.figure import *
import dash
from pathlib import Path
import base64
import uuid
import sys
import re
from flask import request


language = languages["en"]

def set_data_folder():
    platform = sys.platform
    folder = Path("data")
    if platform == "linux":
        folder = Path("/var/spitec/data")
    elif platform == "win32":
        folder = Path("data")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def register_callbacks(app: dash.Dash) -> None:
    FILE_FOLDER = set_data_folder()

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("scale-map-store", "data", allow_duplicate=True),
            Output("relayout-map-store", "data", allow_duplicate=True),
            Output("trajectory-error", "style", allow_duplicate=True),
            Output("projection-radio-store", "data", allow_duplicate=True),
        ],
        [Input("projection-radio", "value")],
        [
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("graph-site-data", "figure"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_map_projection(
        projection_value: ProjectionType,
        show_names_site: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        local_file: str,
        sat: Sat,
        site_data: dict,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, int, None, dict[str, str], ProjectionType]:
        style_traj_error = {"visibility": "hidden"}
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            None,
            None,
            new_points,
        )
        
        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]
        
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )

        if site_map.layout.geo.projection.type != ProjectionType.ORTHOGRAPHIC.value and \
        len(site_data["data"]) != 0:
            style_traj_error = {
                "margin-top": "5px",
                "text-align": "center",
                "fontSize": "16px",
                "color": "red",
            }

        scale_map = 1
        return site_map, scale_map, None, style_traj_error, projection_value

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-map", "clickData"),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-data-store", "data", allow_duplicate=True),
            Output("trajectory-error", "style", allow_duplicate=True),
            Output("sip-tag-time-store", "data", allow_duplicate=True),
        ],
        [Input("graph-site-map", "clickData")],
        [
            State("local-file-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("selection-data-types", "value"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("selection-satellites", "value"),
            State("input-shift", "value"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_site_data(
        clickData: dict[str, list[dict[str, float | str | dict]]],
        local_file: str,
        projection_value: ProjectionType,
        show_names_site: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        data_types: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        sat: Sat,
        shift: float,
        relayout_data: dict[str, float],
        scale_map_store: float,
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, None, bool, dict[str, int], dict[str, str]]:
        style_traj_error = {"visibility": "hidden"}
        if clickData is not None and clickData["points"][0]["curveNumber"] == 0:
            pointIndex = clickData["points"][0]["pointIndex"]
            site_name = list(site_coords.keys())[pointIndex]
            if site_data_store is None:
                site_data_store = {}
            if site_name in site_data_store.keys():
                del site_data_store[site_name]
            else:
                site_data_store[site_name] = pointIndex

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time,
            all_select_sip_tag,
        )

        colors = {}
        for data in site_data.data:
            if data["name"] is None:
                continue
            colors[data.name.lower()] = data.marker.color
        
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        if site_map.layout.geo.projection.type != ProjectionType.ORTHOGRAPHIC.value and \
        len(site_data.data) != 0:
            style_traj_error = {
                "margin-top": "5px",
                "text-align": "center",
                "fontSize": "16px",
                "color": "red",
            }

        disabled = True if len(site_data.data) == 0 else False
        if not site_data_store:
            sip_tag_time = None
        return site_map, None, site_data, disabled, site_data_store, style_traj_error, sip_tag_time

    @app.callback(
        [
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("time-slider-store", "data", allow_duplicate=True),
        ],
        [Input("time-slider", "value")],
        [
            State("selection-data-types", "value"),
            State("site-data-store", "data"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("input-shift", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("input-hm", "value"),
            State("region-site-names-store", "data"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def change_xaxis(
        time_value: list[int],
        data_types: str,
        site_data_store: dict[str, int],
        local_file: str,
        sat: Sat,
        shift: float,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        relayout_data: dict[str, float],
        scale_map_store: float,
        input_hm: float,
        region_site_names: dict[str, int],
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, bool, go.Figure, list[int]]:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time,
            all_select_sip_tag,
        )
        disabled = True if len(site_data.data) == 0 else False

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )

        return site_data, disabled, site_map, time_value

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-data-store", "data", allow_duplicate=True),
            Output("trajectory-error", "style", allow_duplicate=True),
            Output("sip-tag-time-store", "data", allow_duplicate=True),
            Output("all-select-sip-tag", "data", allow_duplicate=True),
        ],
        [Input("clear-all", "n_clicks")],
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("new-points-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def clear_all(
        n: int,
        projection_value: ProjectionType,
        show_names_site: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        relayout_data: dict[str, float],
        scale_map_store: float,
        new_points: dict[str, dict[str, str | float]],
    ) -> list[go.Figure, bool, None, dict[str, str], None]:
        site_data = create_site_data_with_values(
            None, None, None, None, None, None, None, None
        )
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            None,
            relayout_data,
            scale_map_store,
            new_points,
        )
        disabled = True
        style_traj_error = {"visibility": "hidden"}
        return site_map, site_data, disabled, None, style_traj_error, None, None

    @app.callback(
        [
            Output("scale-map-store", "data", allow_duplicate=True),
            Output("relayout-map-store", "data", allow_duplicate=True),
        ],
        Input("graph-site-map", "relayoutData"),
        [
            State("scale-map-store", "data"),
            State("relayout-map-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def change_layout_map(
        relayout_data: dict[str, float],
        scale_map_store: float,
        relayout_data_store: dict[str, float],
    ):
        scale_map = relayout_data.get("geo.projection.scale", scale_map_store)
        if len(relayout_data) == 0 or relayout_data.get("autosize", False):
            relayout_data = relayout_data_store
        return scale_map, relayout_data

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("checkbox-site-store", "data", allow_duplicate=True),
        ],
        [Input("hide-show-site", "value")],
        [
            State("projection-radio", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def hide_show_site(
        show_names_site: bool,
        projection_value: ProjectionType,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, bool]:
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]
        
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_map, show_names_site

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("min-lat", "invalid"),
            Output("max-lat", "invalid"),
            Output("min-lon", "invalid"),
            Output("max-lon", "invalid"),
            Output("region-site-names-store", "data", allow_duplicate=True),
        ],
        [Input("apply-lat-lon", "n_clicks")],
        [
            State("min-lat", "value"),
            State("max-lat", "value"),
            State("min-lon", "value"),
            State("max-lon", "value"),
            State("region-site-names-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def apply_selection_by_region(
        n: int,
        min_lat: int,
        max_lat: int,
        min_lon: int,
        max_lon: int,
        region_site_names: dict[str, int],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | bool | dict[str, int]]:
        return_value_list = [
            None,
            False,
            False,
            False,
            False,
            region_site_names,
        ]
        sites = region_site_names

        check_region_value(min_lat, 1, return_value_list)
        check_region_value(max_lat, 2, return_value_list)
        check_region_value(min_lon, 3, return_value_list)
        check_region_value(max_lon, 4, return_value_list)

        if True in return_value_list or site_coords is None:
            pass
        else:
            sites_by_region = select_sites_by_region(
                site_coords, min_lat, max_lat, min_lon, max_lon
            )
            if len(sites_by_region) > 0:
                tmp_sites, _, _ = get_namelatlon_arrays(sites_by_region)

                keys = list(site_coords.keys())
                sites = dict()
                for site in tmp_sites:
                    sites[site] = keys.index(site)
                return_value_list[-1] = sites
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            sites,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]
        
        return_value_list[0] = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return return_value_list

    def check_region_value(
        value: int,
        idx: int,
        return_value_list: dict[str, go.Figure | bool],
    ) -> None:
        if value is None:
            return_value_list[idx] = True

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("distance", "invalid"),
            Output("center-point-lat", "invalid"),
            Output("center-point-lon", "invalid"),
            Output("region-site-names-store", "data", allow_duplicate=True),
        ],
        [Input("apply-great-circle-distance", "n_clicks")],
        [
            State("distance", "value"),
            State("center-point-lat", "value"),
            State("center-point-lon", "value"),
            State("region-site-names-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def apply_great_circle_distance(
        n: int,
        distance: int,
        lat: int,
        lon: int,
        region_site_names: dict[str, int],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | bool | dict[str, int]]:
        return_value_list = [None, False, False, False, region_site_names]
        sites = region_site_names

        check_region_value(distance, 1, return_value_list)
        check_region_value(lat, 2, return_value_list)
        check_region_value(lon, 3, return_value_list)

        if True in return_value_list or site_coords is None:
            pass
        else:
            central_point = dict()
            central_point[Coordinate.lat.value] = lat
            central_point[Coordinate.lon.value] = lon
            sites_by_region = select_sites_in_circle(
                site_coords, central_point, distance
            )
            if len(sites_by_region) > 0:
                tmp_sites, _, _ = get_namelatlon_arrays(sites_by_region)

                keys = list(site_coords.keys())
                sites = dict()
                for site in tmp_sites:
                    sites[site] = keys.index(site)
                return_value_list[-1] = sites

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            sites,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        return_value_list[0] = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return return_value_list

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("region-site-names-store", "data", allow_duplicate=True),
        ],
        Input("clear-selection-by-region", "n_clicks"),
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def clear_selection_by_region(
        n1: int,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | None]:
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            None,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_map, None
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("name-point", "invalid"),
            Output("point-lat", "invalid"),
            Output("point-lon", "invalid"),
            Output("new-points-store", "data", allow_duplicate=True),
            Output("add-points-error", "style"),
        ],
        [Input("add-point", "n_clicks")],
        [
            State("name-point", "value"),
            State("point-marker", "value"),
            State("point-color", "value"),
            State("point-lat", "value"),
            State("point-lon", "value"),
            State("new-points-store", "data"),
            State("region-site-names-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_new_point(
        n: int,
        point_name: str,
        point_marker: str,
        point_color: str,
        point_lat: int,
        point_lon: int,
        new_points: dict[str, dict[str, str | float]],
        region_site_names: dict[str, int],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | bool | dict[str, dict[str, str | float]], dict[str, str]]:
        return_value_list = [None, False, False, False, new_points]
        points = new_points
        if points is None:
                points = {}

        style = {"visibility": "hidden"}

        check_region_value(point_name, 1, return_value_list)
        check_region_value(point_lat, 2, return_value_list)
        check_region_value(point_lon, 3, return_value_list)

        if True in return_value_list or site_coords is None:
            pass
        elif point_name in points.keys(): 
            style = {
                    "margin-top": "10px",
                    "fontSize": "16px",
                    "color": "red",
                }
        else:
            points[point_name] = {
                "marker": point_marker.lower(),
                "color": point_color,
                "lat": point_lat,
                "lon": point_lon,
            }

        if len(points) == 0:
            points = None

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        return_value_list[0] = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )

        return_value_list[-1] = points
        return_value_list.append(style)
        return return_value_list
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("new-points-store", "data", allow_duplicate=True),
        ],
        Input("delete-all-points", "n_clicks"),
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("region-site-names-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def delete_all_points(
        n1: int,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        region_site_names: dict[str, int],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | None]:
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            None,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_map, None
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("new-points-store", "data", allow_duplicate=True),
        ],
        Input("delete-point", "n_clicks"),
        [
            State("name-point-by-delete", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("region-site-names-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def delete_point(
        n1: int,
        name_point: str,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        region_site_names: dict[str, int],
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | None]:
        if name_point in new_points.keys():
            del new_points[name_point]
        if len(new_points) == 0:
            new_points == None
            
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_map, new_points
    
    @app.callback(
        [
            Output("upload-text", "children", allow_duplicate=True),
            Output("add-trajectory-error", "children", allow_duplicate=True),
            Output("add-trajectory-error", "style", allow_duplicate=True),
            
        ],
        Input("trajectory-file", "filename"),
        Input("trajectory-file", "contents"),
        prevent_initial_call=True,
    )
    def update_upload_text(filename: str, contents):
        error_text = language["tab-add-trajectories"]["error-upload-file"]
        error_style = {"visibility": "hidden"}

        upload_text = language["tab-add-trajectories"]["children"]

        if filename is None:
            error_style = {
                "margin-top": "10px",
                "fontSize": "16px",
                "color": "red",
            }
            error_text = language["tab-add-trajectories"]["error-file"]

        if filename is not None:
            if len(filename) > 20:
                upload_text = filename[:20] + "..."
            else:
                upload_text = filename
        
        return upload_text, error_text, error_style
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("name-trajectory", "invalid"),
            Output("new-trajectories-store", "data", allow_duplicate=True),
            Output("add-trajectory-error", "children", allow_duplicate=True),
            Output("add-trajectory-error", "style"),
        ],
        [Input("add-trajectory", "n_clicks")],
        [
            State("name-trajectory", "value"),
            State("trajectory-file", "contents"),
            State("trajectory-file", "filename"),
            State("trajectory-color", "value"),
            State("new-trajectories-store", "data"),
            State("new-points-store", "data"),
            State("region-site-names-store", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def add_new_trajectory(
        n: int,
        trajectory_name: str,
        file_contents: str,
        filename,
        trajectory_color: str,
        new_trajectories: dict[str, dict[str, float | str]],
        new_points: dict[str, dict[str, str | float]],
        region_site_names: dict[str, int],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | bool | dict[str, dict[str, str | float]], dict[str, str]]:
        error_text = language["tab-add-trajectories"]["error-name"]
        error_style = {"visibility": "hidden"}

        invalid_name = False
        if trajectory_name is None:
            invalid_name = True

        trajectories = new_trajectories
        if trajectories is None:
                trajectories = {}

        if invalid_name or site_coords is None:
            pass
        elif trajectory_name in trajectories.keys():
            error_style = {
                "margin-top": "10px",
                "fontSize": "16px",
                "color": "red",
            }
        elif file_contents is None:
                error_text = language["tab-add-trajectories"]["error-upload-file"]
                error_style = {
                    "margin-top": "10px",
                    "fontSize": "16px",
                    "color": "red",
                }
        else:
            try:
                local_file_path = Path(local_file)

                content_type, content_string = file_contents.split(',')
                decoded = base64.b64decode(content_string)
                data_string = decoded.decode('utf-8')
            
                lines = data_string.strip().split('\n')
                data_rows = [line.split(',') for line in lines[1:]]  # Получаем данные без загаловков
                times, lons, lats, hms = [], [], [], []
                for row in data_rows:
                    traj_time_str = datetime.strptime(
                        f"{local_file_path.stem} {row[0]}","%Y-%m-%d %H:%M:%S"
                    )
                    traj_time = traj_time_str.replace(tzinfo=timezone.utc)
                    
                    times.append(traj_time)
                    lons.append(float(row[1]))
                    lats.append(float(row[2]))
                    hms.append(float(row[3]))

                traj = Trajectorie(trajectory_name, None, None, None)
                traj.traj_lat = np.array(lats, dtype=object)
                traj.traj_lon = np.array(lons, dtype=object)
                traj.times = np.array(times)
                traj.traj_hm = np.array(hms, dtype=object)
                
                traj.adding_artificial_value()

                trajectories[trajectory_name] = {
                    "times": traj.times,
                    "traj_lat": traj.traj_lat,
                    "traj_lon": traj.traj_lon ,
                    "traj_hm": traj.traj_hm,
                    "color": trajectory_color,
                }
            except Exception:
                error_text = [
                    language["tab-add-trajectories"]["error-file"],
                    ". ",
                    language["tab-add-trajectories"]["example"],
                    html.Br(),
                    language["tab-add-trajectories"]["format"],
                    html.Br(),
                    language["tab-add-trajectories"]["format-example"]
                ]
                error_style = {
                    "margin-top": "10px",
                    "fontSize": "14px",
                    "color": "red",
                }

        if len(trajectories) == 0:
            trajectories = None

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            trajectories,
        )

        return site_map, invalid_name, trajectories, error_text, error_style
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("new-trajectories-store", "data", allow_duplicate=True),
        ],
        Input("delete-all-trajectories", "n_clicks"),
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("region-site-names-store", "data"),
            State("new-points-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def delete_all_new_trajectories(
        n1: int,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        region_site_names: dict[str, int],
        new_points: dict[str, dict[str, str | float]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | None]:
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            None
        )
        return site_map, None
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("new-trajectories-store", "data", allow_duplicate=True),
        ],
        Input("delete-trajectory", "n_clicks"),
        [
            State("name-trajectory-by-delete", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("local-file-store", "data"),
            State("selection-satellites", "value"),
            State("time-slider", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("region-site-names-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def delete_trajectory_by_name(
        n1: int,
        name_trajectory: str,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        local_file: str,
        sat: Sat,
        time_value: list[int],
        input_hm: float,
        sip_tag_time: dict,
        region_site_names: dict[str, int],
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | None]:
        if new_trajectories is not None and name_trajectory in new_trajectories.keys():
            del new_trajectories[name_trajectory]
            if len(new_trajectories) == 0:
                new_trajectories == None
            
        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_map, new_trajectories

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
            Output("downloading-file-store", "data", allow_duplicate=True),
            Output("boot-process", "value", allow_duplicate=True),
            Output("load-per", "children", allow_duplicate=True),
        ],
        [Input("boot-progress-window", "is_open")],
        [
            State("downloading-file-store", "data"),
            State("boot-process", "value"),
            State("load-per", "children"),
        ],
        prevent_initial_call=True,
    )
    def delete_incomplete_file(
        is_open: bool,
        incomplete_file: str,
        boot_process_value: int,
        per_value: str,
    ) -> list[None | str | int]:
        if not is_open:
            if incomplete_file is not None:
                local_file = FILE_FOLDER / (incomplete_file + ".h5")
                try:
                    f = h5py.File(local_file)
                    f.close
                except:
                    local_file.unlink()
            return None, 0, "0%"
        return incomplete_file, boot_process_value, per_value

    @app.callback(
        [
            Output("downloaded", "style", allow_duplicate=True),
            Output("downloaded", "children", allow_duplicate=True),
        ],
        [Input("download-file", "n_clicks")],
        [State("date-selection", "date")],
        background=True,
        running=[
            (Output("boot-progress-window", "is_open"), True, True),
            (Output("boot-progress-window", "backdrop"), "static", True),
            (Output("download-window", "is_open"), False, False),
            (
                Output("loading-process-modal-header", "close_button"),
                False,
                True,
            ),
            (Output("cancel-download", "disabled"), False, True),
        ],
        cancel=Input("cancel-download", "n_clicks"),
        progress=[
            Output("boot-process", "value"),
            Output("load-per", "children"),
        ],
        prevent_initial_call=True,
    )
    def download_file(
        set_progress, n1: int, date: str
    ) -> list[dict[str, str] | str]:
        text = language["download_window"]["successаfuly"]
        color = "green"
        if date is None:
            text = language["download_window"]["unsuccessаfuly"]
        else:
            local_file = FILE_FOLDER / (date + ".h5")
            if local_file.exists():
                text = language["download_window"]["repeat-action"]
            else:
                local_file.touch()
                try:
                    for done in load_data(date, local_file):
                        set_progress((done, f"{done}%"))
                except requests.exceptions.HTTPError as err:
                    text = language["download_window"]["error"]
                    local_file.unlink()
        if text != language["download_window"]["successаfuly"]:
            color = "red"
        style = {
            "text-align": "center",
            "margin-top": "10px",
            "color": color,
        }
        return style, text

    @app.callback(
        Output("downloading-file-store", "data"),
        [Input("cancel-download", "n_clicks")],
        [State("date-selection", "date")],
        prevent_initial_call=True,
    )
    def save_file_name(n: int, date: str) -> str:
        if date is not None:
            return date
        return None

    @app.callback(
        Output("file-size", "children"),
        [Input("check-file-size", "n_clicks")],
        [State("date-selection", "date")],
        prevent_initial_call=True,
    )
    def check_file_size(n: int, date: str) -> str:
        text = language["download_window"]["file-size"]
        if date is None:
            text += "none"
        else:
            Mb = сheck_file_size(date)
            if Mb is None:
                text += "none"
            elif Mb == 0:
                text += language["download_window"]["unknown"]
            else:
                text += str(Mb)
        return text

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
                if file_path.is_file() and file_path.name.endswith('.h5'):
                    options.append(
                        {"label": file_path.name, "value": file_path.name}
                    )
        return not is_open, options

    @app.callback(
        [
            Output("open-window", "is_open"),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("local-file-store", "data", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-coords-store", "data", allow_duplicate=True),
            Output("region-site-names-store", "data", allow_duplicate=True),
            Output("site-data-store", "data", allow_duplicate=True),
            Output("selection-satellites", "options", allow_duplicate=True),
            Output("satellites-options-store", "data", allow_duplicate=True),
            Output("scale-map-store", "data", allow_duplicate=True),
            Output("relayout-map-store", "data", allow_duplicate=True),
            Output("sip-tag-time-store", "data", allow_duplicate=True),
            Output("new-points-store", "data", allow_duplicate=True),
            Output("new-trajectories-store", "data", allow_duplicate=True),
            Output("all-select-sip-tag", "data", allow_duplicate=True),
            Output("selection-events", "options", allow_duplicate=True),
            Output("events-options-store", "data", allow_duplicate=True),
        ],
        [Input("open-file", "n_clicks")],
        [
            State("select-file", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
        ],
        prevent_initial_call=True,
    )
    def open_file(
        n1: int,
        filename: str,
        projection_value: ProjectionType,
        show_names_site: bool,
    ) -> list[
        bool
        | go.Figure
        | str
        | dict[Site, dict[Coordinate, float]]
        | None
        | list[dict[str, str]]
    ]:
        local_file = FILE_FOLDER / filename
        site_coords = get_sites_coords(local_file)

        site_map = create_map_with_points(
            site_coords, projection_value, show_names_site, None, None, None, None, None
        )
        site_data = create_site_data()
        satellites = get_satellites(local_file)
        options = [{"label": sat, "value": sat} for sat in satellites]

        events_options = []
        option_data = load_data_json(Path("events.json"))
        if option_data is None:
            events_options = dash.no_update
        else:
            events_options = [
                {"label": key, "value": key} for key in option_data.keys()
            ]

        scale_map = 1
        return (
            False,
            site_map,
            str(local_file),
            site_data,
            True,
            site_coords,
            None,
            None,
            options,
            options,
            scale_map,
            None,
            None,
            None,
            None,
            None,
            events_options,
            events_options
        )
    
    @app.callback(
        [
            Output("share-window", "is_open", allow_duplicate=True),
            Output("link", "value"),
            Output("copy-link", "children", allow_duplicate=True),
            Output('session-id-store', 'data', allow_duplicate=True),
            Output('current-session-id', 'data', allow_duplicate=True),
            Output('input-email', 'invalid', allow_duplicate=True)
        ],
        [Input("share", "n_clicks")],
        [
            State("share-window", "is_open"),
            State('session-id-store', 'data'),

            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("local-file-store", "data"),
            State("time-slider", "value"),
            State("selection-data-types", "value"),
            State("satellites-options-store", "data"),
            State("events-options-store", "data"),
            State("selection-satellites", "value"),
            State("selection-events", "value"),
            State("input-shift", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),

            State("input-email", "value"),
        ],
        prevent_initial_call=True,
    )
    def open_close_share_window(
        n1: int,
        is_open: bool,
        session_id_store: dict[str, str],

        projection_value: ProjectionType,
        show_names_site: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        local_file: str,
        time_value: list[int],
        data_types: str,
        satellites_options: list[dict[str, str]],
        events_options: list[dict[str, str]],
        sat: Sat,
        event: str,
        shift: float,
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
        input_email: str, 
    ) -> list[bool, str, html.I, dict[str, str], str]:

        if input_email is None or \
            not re.match(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", input_email):
            return_value = [dash.no_update for _ in range(5)]
            return_value.append(True)
            return return_value
        
        session_id = None
        base_url = get_base_url() 

        data_to_save = {
            "projection": projection_value,
            "show_names_site": show_names_site,
            "region_site_names": region_site_names,
            "site_coords": site_coords,
            "site_data_store": site_data_store,
            "file_name": local_file,
            "time_limit": time_value,
            "data_type": data_types,
            "satellites_options": satellites_options,
            "events_options": events_options,
            "sat": sat,
            "event": event,
            "shift": shift,
            "hm": input_hm,
            "sip_tag": sip_tag_time,
            "user_points": new_points,
            "user_trajectories": new_trajectories,
            "events": all_select_sip_tag,
        }
        file_folder_json = (FILE_FOLDER / "json")
        file_folder_json.mkdir(parents=True, exist_ok=True)
        
        new_file_hash = calculate_json_hash(data_to_save)
        if session_id_store is None:
            session_id_store = {}

            session_id = str(uuid.uuid4()) 
            file_name = (FILE_FOLDER / "json") / f"{session_id}.json"
            save_data_json(file_name, data_to_save)
            session_id_store[session_id] = new_file_hash
        else:
            session_id_exists = False
            for key, value in session_id_store.items():
                if new_file_hash == value:
                    session_id = key
                    session_id_exists = True
                    break

            if not session_id_exists:
                session_id = str(uuid.uuid4()) 
                file_name = (FILE_FOLDER / "json") / f"{session_id}.json"
                save_data_json(file_name, data_to_save)
                session_id_store[session_id] = new_file_hash
        
        link = f"{base_url}session_id={session_id}"
        if not is_open:
            icon = html.I(className="fas fa-copy")
        else:
            icon = html.I(className="fas fa-check")
        return True, link, icon, session_id_store, session_id, False

    def get_base_url():
        part_url = request.host_url.split("://")
        proto = request.headers.get('X-Forwarded-Proto', request.scheme)
        base_url = proto + "://" + part_url[1]
        return base_url
    
    @app.callback(
        [
            Output("share-window", "is_open", allow_duplicate=True),
            Output("download-data", "data"),
        ],
        Input("upload-data", "n_clicks"),
        [
            State('current-session-id', 'data'),
            State("graph-site-data", "figure"),
            State("input-email", "value"),
        ],
        prevent_initial_call=True,
    )
    def upload_data(
        n: int,
        current_session_id: str,
        site_data: go.Figure,
        input_email: str,
    ) -> bool:
        if current_session_id is None:
            return False, dash.no_update
        
        file_name = (FILE_FOLDER / "json") / f"{current_session_id}.json"
        session_data = load_data_json(file_name)

        base_url = get_base_url()
        session_data["email"] = input_email
        session_data["link"] = f"{base_url}session_id={current_session_id}"
        session_data["site_data"] = []
        for data in site_data["data"]:
            tmp_data = {
                "site": data["name"].lower(),
                "times": data["x"],
                "data": data["customdata"],
            }
            session_data["site_data"].append(tmp_data)
        json_data = json.dumps(session_data)
        return False, dict(content=json_data, filename="spitec.json")
    
    app.clientside_callback(
        """
        function(n_clicks, text) {
            if (n_clicks > 0) {
                navigator.clipboard.writeText(text);
                return window.dash_clientside.no_update;
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('session-id-store', 'data'),
        Input('copy-link', 'n_clicks'),
        State('link', 'value'),
    )

    @app.callback(
        Output("copy-link", "children", allow_duplicate=True),
        Input('copy-link', 'n_clicks'),
        prevent_initial_call=True,
    )
    def successful_copying(n: int) -> html.I:
        return html.I(className="fas fa-check")

    @app.callback(
        [
            Output("input-shift", "value", allow_duplicate=True),
            Output("selection-data-types-store", "data", allow_duplicate=True),
        ],
        Input("selection-data-types", "value"),
        State("input-shift", "value"),
        prevent_initial_call=True,
    )
    def change_data_types(
        data_types: str,
        shift: float,
    ) -> list[float, str]:
        val_shift = shift
        if shift == 0 or shift == -0.5 or shift == -1:
            if data_types in [
                DataProducts.roti.name, 
                DataProducts.dtec_2_10.name, 
                DataProducts.dtec_10_20.name
            ]:
                val_shift = -0.5
            else:
                val_shift = -1
        return val_shift, data_types
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("input-hm-store", "data", allow_duplicate=True),
        ],
        [Input("input-hm", "value")],
        [
            State("selection-satellites", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("region-site-names-store", "data"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def change_hm(
        input_hm: float,
        sat: Sat,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        region_site_names: dict[str, int],
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, float]:
        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_map, input_hm
    
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("sip-tag-time-store", "data", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
         ],
        [Input("show-tag-sip", "n_clicks")],
        [
            State("input-sip-tag-time", "value"),
            State("input-hm", "value"),
            State("selection-satellites", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("graph-site-data", "figure"),
            State("region-site-names-store", "data"),
            State("selection-data-types", "value"),
            State("input-shift", "value"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def show_sip_tag(
        n: int,
        sip_tag_time: str,
        input_hm: float,
        sat: Sat,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        relayout_data: dict[str, float],
        scale_map_store: float,
        site_data: dict,
        region_site_names: dict[str, int],
        data_types: str,
        shift: float,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | dict]:
        sip_tag_time_dict = {
            "name": None,
            "marker": "star",
            "color": None,
            "time": sip_tag_time,
            "site": "",
            "coords": []
        }
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time_dict,
            all_select_sip_tag,
        )

        colors = {}
        for data in site_data.data:
            if data["name"] is None:
                continue
            colors[data.name.lower()] = data.marker.color

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time_dict,
            all_select_sip_tag,
            new_trajectories,
        )
        if not site_data_store:
            sip_tag_time_dict = None
        return site_map, sip_tag_time_dict, site_data
    
    @app.callback(
        [
            Output("geo-stuctures-window", "is_open", allow_duplicate=True),
            Output("radio-container", "children", allow_duplicate=True),
            Output("current-select-sip-tag", "data", allow_duplicate=True)
        ],
        Input("graph-site-data", "clickData"),
        State("selection-events", "value"),
        prevent_initial_call=True,
    )
    def open_close_new_sip_tag(
        clickData: dict[str, list[dict[str, float | str | dict]]],
        event: str,
    ) -> list[
        bool, 
        list[dict[str, str | int]], 
        dict[str, list[dict[str, float | str | dict]]]
    ]:
        if clickData["points"][0]['customdata'] == 0 or event is None:
            return [False, dash.no_update, None]
        
        options = []
        option_data = load_data_json(Path("events.json"))
        if option_data is None:
            return [dash.no_update, dash.no_update, dash.no_update]
        
        options = [
            {
                "label": structure["name"], "value": i
            } for i, structure in enumerate(option_data[event])
        ]

        radio_items = dcc.RadioItems(
            id='dynamic-radio',
            options=options,
            labelStyle={'display': 'flex', "gap": "10px", 'margin-bottom': '5px'}
        )
        return [True, radio_items, clickData]
    
    @app.callback(
        Output("geo-stuctures-window", "is_open", allow_duplicate=True),
        Input("cancel-radio", "n_clicks"),
        prevent_initial_call=True,
    )
    def cancel_radio(n: int):
        return False
    
    @app.callback(
        [
            Output("geo-stuctures-window", "is_open", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("all-select-sip-tag", "data", allow_duplicate=True),
        ],
        Input("dynamic-radio", "value"),
        [
            State("selection-satellites", "value"),
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("input-shift", "value"),
            State("sip-tag-time-store", "data"),
            State("current-select-sip-tag", "data"),
            State("all-select-sip-tag", "data"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("region-site-names-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("input-hm", "value"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("selection-events", "value"),
        ],
        prevent_initial_call=True,
    )
    def select_new_sip_tag(
        idx_geo_stucture: str,
        sat: Sat,
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        shift: float,
        sip_tag_time: dict,
        clickData: dict[str, list[dict[str, float | str | dict]]],
        all_select_sip_tag: list[dict],
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        region_site_names: dict[str, int],
        relayout_data: dict[str, float],
        scale_map_store: float,
        input_hm: float,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        event: str,
    ) -> list[go.Figure | list[dict]]:
        if clickData is None or idx_geo_stucture is None:
            is_open = True
            if clickData is None:
                is_open = False
            return [is_open, dash.no_update, dash.no_update, dash.no_update]
        
        point = clickData["points"][0]

        if all_select_sip_tag is None:
            all_select_sip_tag = []

        data = load_data_json(Path("events.json"))
        geo_stucture = data[event][int(idx_geo_stucture)].copy()
        
        index = -1
        try:
            index = next(
                    filter(
                        lambda i_d: all_select_sip_tag[i_d]['name'] == geo_stucture["name"], range(
                            len(all_select_sip_tag)
                        )
                    ), -1
                )
        except:
            pass
        
        if index != -1:
            all_select_sip_tag.pop(index)
            
        geo_stucture["time"] = change_time(point["x"])
        geo_stucture["data"] = point['customdata']
        geo_stucture["data_types"] = data_types
        geo_stucture["event"] = event
        geo_stucture["site"] = list(site_data_store.keys())[point['curveNumber']]
        all_select_sip_tag.append(geo_stucture)
        
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time, 
            all_select_sip_tag,
        )
        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return [False, site_data, site_map, all_select_sip_tag]
    
    def change_time(point_x: str) -> str:
        x_time = point_x
        if len(point_x) == 16:
            x_time += ":00"
        elif len(point_x) == 13:
            x_time += ":00:00"
        elif len(point_x) == 10:
            x_time += " 00:00:00"
        return x_time

    @app.callback(
        [
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("satellite-store", "data", allow_duplicate=True),
        ],
        [Input("selection-satellites", "value")],
        [
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("input-shift", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("input-hm", "value"),
            State("region-site-names-store", "data"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def change_satellite(
        sat: Sat,
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        shift: float,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        relayout_data: dict[str, float],
        scale_map_store: float,
        input_hm: float,
        region_site_names: dict[str, int],
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, go.Figure, Sat]:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time,
            all_select_sip_tag,
        )
        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            all_select_sip_tag,
            new_trajectories,
        )
        return site_data, site_map, sat
    
    @app.callback(
        [
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("event-store", "data", allow_duplicate=True),
            Output("all-select-sip-tag", "data", allow_duplicate=True),
        ],
        [Input("selection-events", "value")],
        [
            State("selection-satellites", "value"),
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("input-shift", "value"),
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("site-coords-store", "data"),
            State("relayout-map-store", "data"),
            State("scale-map-store", "data"),
            State("input-hm", "value"),
            State("region-site-names-store", "data"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("event-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def change_event(
        event: str,
        sat: Sat,
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        shift: float,
        projection_value: ProjectionType,
        show_names_site: bool,
        site_coords: dict[Site, dict[Coordinate, float]],
        relayout_data: dict[str, float],
        scale_map_store: float,
        input_hm: float,
        region_site_names: dict[str, int],
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        event_store: str,
    ) -> list[go.Figure, go.Figure, str, None]:
        if event_store == event:
            return [dash.no_update, dash.no_update, dash.no_update, dash.no_update]
        
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time,
            None,
        )
        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_points(
            site_coords,
            projection_value,
            show_names_site,
            region_site_names,
            site_data_store,
            relayout_data,
            scale_map_store,
            new_points,
        )
        site_map = create_map_with_trajectories(
            site_map,
            local_file,
            site_data_store,
            site_coords,
            sat, 
            colors,
            time_value,
            input_hm,
            sip_tag_time,
            None,
            new_trajectories,
        )
        return site_data, site_map, event, None

    @app.callback(
        [
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("input-shift-store", "data", allow_duplicate=True),
        ],
        [Input("input-shift", "value")],
        [
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("selection-satellites", "value"),
            State("sip-tag-time-store", "data"),
            State("all-select-sip-tag", "data"),
        ],
        prevent_initial_call=True,
    )
    def change_shift(
        shift: float,
        data_types: str,
        local_file: str,
        site_data_store: dict[str, int],
        time_value: list[int],
        sat: Sat,
        sip_tag_time: dict,
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure, float]:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time,
            all_select_sip_tag,
        )
        return site_data, shift

    @app.callback(
        [
            Output("graph-site-map", "figure"),
            Output("graph-site-data", "figure"),
            Output("time-slider", "disabled"),
            Output("selection-satellites", "options"),
            Output("selection-events", "options"),
            Output("scale-map-store", "data"),
            Output("relayout-map-store", "data"),
            Output("trajectory-error", "style"),
            Output("is-link-store", "data"),

            Output("projection-radio", "value"),
            Output("hide-show-site", "value"),
            Output("region-site-names-store", "data"),
            Output("site-coords-store", "data"),
            Output("site-data-store", "data"),
            Output("local-file-store", "data"),
            Output("time-slider", "value"),
            Output("selection-data-types", "value"),
            Output("satellites-options-store", "data"),
            Output("events-options-store", "data"),
            Output("selection-satellites", "value"),
            Output("selection-events", "value"),
            Output("input-shift", "value"),
            Output("input-hm", "value"),
            Output("sip-tag-time-store", "data"),
            Output("new-points-store", "data"),
            Output("new-trajectories-store", "data"),
            Output("all-select-sip-tag", "data"),

            Output("projection-radio-store", "data"),
            Output("checkbox-site-store", "data"),
            Output("time-slider-store", "data"),
            Output("selection-data-types-store", "data"),
            Output("satellite-store", "data"),
            Output("event-store", "data"),
            Output("input-shift-store", "data"),
            Output("input-hm-store", "data"),
        ],
        [Input("url", "pathname")],
        [
            State("projection-radio", "value"),
            State("hide-show-site", "value"),
            State("region-site-names-store", "data"),
            State("site-coords-store", "data"),
            State("site-data-store", "data"),
            State("local-file-store", "data"),
            State("time-slider", "value"),
            State("selection-data-types", "value"),
            State("satellites-options-store", "data"),
            State("events-options-store", "data"),
            State("selection-satellites", "value"),
            State("selection-events", "value"),
            State("input-shift", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
            State("new-trajectories-store", "data"),
            State("is-link-store", "data"),

            State("projection-radio-store", "data"),
            State("checkbox-site-store", "data"),
            State("time-slider-store", "data"),
            State("selection-data-types-store", "data"),
            State("satellite-store", "data"),
            State("event-store", "data"),
            State("input-shift-store", "data"),
            State("input-hm-store", "data"),

            State("all-select-sip-tag", "data"),
        ],
    )
    def update_all(
        pathname: str,
        projection_value: ProjectionType,
        show_names_site: bool,
        region_site_names: dict[str, int],
        site_coords: dict[Site, dict[Coordinate, float]],
        site_data_store: dict[str, int],
        local_file: str,
        time_value: list[int],
        data_types: str,
        satellites_options: list[dict[str, str]],
        events_options: list[dict[str, str]],
        sat: Sat,
        event: str,
        shift: float,
        input_hm: float,
        sip_tag_time: dict,
        new_points: dict[str, dict[str, str | float]],
        new_trajectories: dict[str, dict[str, float | str]],
        is_link: bool,

        projection_radio_store: str,
        checkbox_site_store: bool,
        time_slider_store: bool,
        selection_data_types_store: str,
        satellite_store: Sat,
        event_store: str,
        input_shift_store: float,
        input_hm_store: float,
        all_select_sip_tag: list[dict],
    ) -> list[go.Figure | bool | list[dict[str, str]] | dict[str, str]]:
        no_update = True

        if is_link:
            projection_value = projection_radio_store
            show_names_site = checkbox_site_store
            time_value = time_slider_store
            data_types = selection_data_types_store
            sat = satellite_store
            event = event_store
            shift = input_shift_store
            input_hm = input_hm_store
        elif not is_link and pathname is not None and pathname != "/":
            is_link = True
            session_id = pathname.split("=")[1]
            file_name = (FILE_FOLDER / "json") / f"{session_id}.json"
            session_data = load_data_json(file_name)

            projection_value = session_data["projection"]
            show_names_site = session_data["show_names_site"]
            region_site_names = session_data["region_site_names"]
            site_coords = session_data["site_coords"]
            site_data_store = session_data["site_data_store"]
            local_file = session_data["file_name"]
            time_value = session_data["time_limit"]
            data_types = session_data["data_type"]
            satellites_options = session_data["satellites_options"]
            events_options = session_data["events_options"]
            sat = session_data["sat"]
            event = session_data["event"]
            shift = session_data["shift"]
            input_hm = session_data["hm"]
            sip_tag_time = session_data["sip_tag"]
            new_points = session_data["user_points"]
            new_trajectories = session_data["user_trajectories"]
            all_select_sip_tag = session_data["events"]
            no_update = False
        
        dash_update = {
                "projection_value": projection_value,
                "show_names_site": show_names_site,
                "region_site_names": region_site_names,
                "site_coords": site_coords,
                "site_data_store": site_data_store,
                "local_file": local_file,
                "time_value": time_value,
                "data_types": data_types,
                "satellites_options": satellites_options,
                "events_options": events_options,
                "sat": sat,
                "event": event,
                "shift": shift,
                "input_hm": input_hm,
                "sip_tag_time": sip_tag_time,
                "new_points": new_points,
                "new_trajectories": new_trajectories,
                "all_select_sip_tag": all_select_sip_tag,
        }

        satellites_options, events_options, style_traj_error, site_map, site_data, disabled, scale_map = main_update(
            dash_update
        )
        return_list = [
            site_map,
            site_data, 
            disabled, 
            satellites_options, 
            events_options,
            scale_map, 
            None, 
            style_traj_error, 
            is_link
        ]
        if no_update and not is_link: # обновление не в "share"
            dash_no_update = [dash.no_update for _ in range(26)]
            return_list.extend(dash_no_update)
            return return_list
        elif no_update and is_link: # обновление в "share" НЕ в первую загрузку
            return_list.extend([projection_value, show_names_site]) # обновляем value

            dash_no_update = [dash.no_update for _ in range(4)]
            return_list.extend(dash_no_update)

            return_list.extend([
                time_value,
                data_types,
                dash.no_update,
                dash.no_update,
                sat,
                event,
                shift,
                input_hm,
            ])

            dash_no_update = [dash.no_update for _ in range(12)]
            return_list.extend(dash_no_update)
            return return_list
        else: # обновление в "share" в первую загрузку
            return_list.extend(list(dash_update.values()))
            return_list.extend([  # обновляем store
                projection_value, 
                show_names_site, 
                time_value, 
                data_types, 
                sat, 
                event,
                shift, 
                input_hm
            ])
            return return_list

    def main_update(
        dash_update: dict
    ) -> list:
        style_traj_error = {"visibility": "hidden"}
        site_map = create_map_with_points(
            dash_update["site_coords"],
            dash_update["projection_value"],
            dash_update["show_names_site"],
            dash_update["region_site_names"],
            dash_update["site_data_store"],
            None,
            None,
            dash_update["new_points"],
        )
        site_data = create_site_data_with_values(
            dash_update["site_data_store"],
            dash_update["sat"],
            dash_update["data_types"],
            dash_update["local_file"],
            dash_update["time_value"],
            dash_update["shift"],
            dash_update["sip_tag_time"],
            dash_update["all_select_sip_tag"],
        )

        colors = {}
        for data in site_data["data"]:
            if data["name"] is None:
                continue
            colors[data["name"].lower()] = data["marker"]["color"]

        site_map = create_map_with_trajectories(
            site_map,
            dash_update["local_file"],
            dash_update["site_data_store"],
            dash_update["site_coords"],
            dash_update["sat"], 
            colors,
            dash_update["time_value"],
            dash_update["input_hm"],
            dash_update["sip_tag_time"],
            dash_update["all_select_sip_tag"],
            dash_update["new_trajectories"],
        )
            
        disabled = True if len(site_data.data) == 0 else False
        if dash_update["satellites_options"] is None:
            satellites_options = []
        else:
            satellites_options = dash_update["satellites_options"]

        if dash_update["events_options"] is None:
            events_options = []
        else:
            events_options = dash_update["events_options"]
        scale_map = 1

        if site_map.layout.geo.projection.type != ProjectionType.ORTHOGRAPHIC.value and \
        len(site_data.data) != 0:
            style_traj_error = {
                "margin-top": "5px",
                "text-align": "center",
                "fontSize": "16px",
                "color": "red",
            }
            
        return satellites_options,events_options,style_traj_error,site_map,site_data,disabled,scale_map
