from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from ..view import *
from ..processing import *
from .figure import *
import dash
from pathlib import Path


language = languages["en"]
FILE_FOLDER = Path("data")


def register_callbacks(app: dash.Dash) -> None:
    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("scale-map-store", "data", allow_duplicate=True),
            Output("relayout-map-store", "data", allow_duplicate=True),
            Output("trajectory-error", "style", allow_duplicate=True),
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
    ) -> list[go.Figure, int, None, dict[str, str]]:
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
        return site_map, scale_map, None, style_traj_error

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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
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
            sip_tag_time
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
    ) -> list[go.Figure | bool]:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time
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
        )

        return site_data, disabled, site_map

    @app.callback(
        [
            Output("graph-site-map", "figure", allow_duplicate=True),
            Output("graph-site-data", "figure", allow_duplicate=True),
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-data-store", "data", allow_duplicate=True),
            Output("trajectory-error", "style", allow_duplicate=True),
            Output("sip-tag-time-store", "data", allow_duplicate=True),
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
            None, None, None, None, None, None, None
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
        return site_map, site_data, disabled, None, style_traj_error, None

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
        Output("graph-site-map", "figure", allow_duplicate=True),
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
    ) -> go.Figure:
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
        )
        return site_map

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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
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
        sip_tag_time: str,
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
        sip_tag_time: str,
        region_site_names: dict[str, int],
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
        )
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
            if not FILE_FOLDER.exists():
                FILE_FOLDER.mkdir()
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
            Output("time-slider", "disabled", allow_duplicate=True),
            Output("site-coords-store", "data"),
            Output("region-site-names-store", "data"),
            Output("site-data-store", "data"),
            Output("selection-satellites", "options", allow_duplicate=True),
            Output("satellites-options-store", "data"),
            Output("scale-map-store", "data", allow_duplicate=True),
            Output("relayout-map-store", "data", allow_duplicate=True),
            Output("sip-tag-time-store", "data", allow_duplicate=True),
            Output("new-points-store", "data", allow_duplicate=True),
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
        )

    @app.callback(
        Output("input-shift", "value", allow_duplicate=True),
        Input("selection-data-types", "value"),
        State("input-shift", "value"),
        prevent_initial_call=True,
    )
    def change_data_types(
        data_types: str,
        shift: float,
    ) -> float:
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
        return val_shift
    
    @app.callback(
        Output("graph-site-map", "figure", allow_duplicate=True),
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
    ) -> go.Figure:
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
        )
        return site_map
    
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
    ) -> go.Figure:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time
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
            sip_tag_time
        )
        if not site_data_store:
            sip_tag_time = None
        return site_map, sip_tag_time, site_data

    @app.callback(
        [Output("graph-site-data", "figure", allow_duplicate=True),
         Output("graph-site-map", "figure", allow_duplicate=True),],
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
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
    ) -> go.Figure:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time
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
        )
        return site_data, site_map

    @app.callback(
        Output("graph-site-data", "figure", allow_duplicate=True),
        [Input("input-shift", "value")],
        [
            State("selection-data-types", "value"),
            State("local-file-store", "data"),
            State("site-data-store", "data"),
            State("time-slider", "value"),
            State("selection-satellites", "value"),
            State("sip-tag-time-store", "data"),
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
        sip_tag_time: str,
    ) -> go.Figure:
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time
        )
        return site_data

    @app.callback(
        [
            Output("graph-site-map", "figure"),
            Output("graph-site-data", "figure"),
            Output("time-slider", "disabled"),
            Output("selection-satellites", "options"),
            Output("scale-map-store", "data"),
            Output("relayout-map-store", "data"),
            Output("trajectory-error", "style"),
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
            State("selection-satellites", "value"),
            State("input-shift", "value"),
            State("input-hm", "value"),
            State("sip-tag-time-store", "data"),
            State("new-points-store", "data"),
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
        sat: Sat,
        shift: float,
        input_hm: float,
        sip_tag_time: str,
        new_points: dict[str, dict[str, str | float]],
    ) -> list[go.Figure, bool, list[dict[str, str]], dict[str, str]]:
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
        site_data = create_site_data_with_values(
            site_data_store,
            sat,
            data_types,
            local_file,
            time_value,
            shift,
            sip_tag_time
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
            sip_tag_time
        )
            
        disabled = True if len(site_data.data) == 0 else False
        if satellites_options is None:
            satellites_options = []
        scale_map = 1

        if site_map.layout.geo.projection.type != ProjectionType.ORTHOGRAPHIC.value and \
        len(site_data.data) != 0:
            style_traj_error = {
                "margin-top": "5px",
                "text-align": "center",
                "fontSize": "16px",
                "color": "red",
            }

        return (
            site_map,
            site_data,
            disabled,
            satellites_options,
            scale_map,
            None,
            style_traj_error
        )