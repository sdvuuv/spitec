from ..view import *
from ..processing import *
from datetime import datetime, timezone

SHIFT = -0.5

def create_map_with_sites(
        site_coords: dict[Site, dict[Coordinate, float]],
        projection_value: ProjectionType,
        check_value: bool, 
        region_site_names: list[str],
        site_data_store: list[str],
    ) -> go.Figure:
    site_map = create_site_map()

    if projection_value != site_map.layout.geo.projection.type:
        site_map.update_layout(geo=dict(projection_type=projection_value))

    if check_value:
        site_map.data[0].mode = "markers+text"
    else:
        site_map.data[0].mode = "markers"

    if site_coords is not None:
        site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

        colors = np.array([PointColor.SILVER.value] * site_array.shape[0])

        site_map.data[0].lat = lat_array
        site_map.data[0].lon = lon_array
        site_map.data[0].text = [site.upper() for site in site_array]
        site_map.data[0].marker.color = colors
        
        _change_points_on_map(region_site_names, site_data_store, site_map)
    return site_map

def _change_points_on_map(
    sites: list[str],
    site_data_store: list[str],
    site_map: go.Figure
) -> None:
    colors = site_map.data[0].marker.color.copy()
    for i, site in enumerate(site_map.data[0].text):
        if sites is not None:
            if site.lower() in sites:
                if colors[i] == PointColor.SILVER.value:
                    colors[i] = PointColor.GREEN.value
            elif colors[i] == PointColor.GREEN.value:
                colors[i] = PointColor.SILVER.value

        if site_data_store is not None:
            if site in site_data_store:
                colors[i] = PointColor.RED.value
            
    site_map.data[0].marker.color = colors


def create_site_data_with_values(
        site_data_store: list[str],
        data_types: str,
        local_file: str,
        time_value: list[int]
    ) -> go.Figure:
    site_data = create_site_data()
    
    if site_data_store is not None:
        dataproduct = _define_data_type(data_types)
        for name in site_data_store:
            _add_line(site_data, name.lower(), dataproduct, local_file)
    if len(site_data.data) != 0:
        limit = create_limit_xaxis(time_value, site_data)
        site_data.update_layout(xaxis=dict(range=[limit[0], limit[1]]))
    return site_data

def create_limit_xaxis(time_value: list[int], site_data: go.Figure) -> tuple[datetime]:
    date = site_data.data[0].x[0]

    hour_start_limit = 23 if time_value[0] == 24 else time_value[0]
    minute_start_limit = 59 if time_value[0] == 24 else 0
    second_start_limit = 59 if time_value[0] == 24 else 0

    hour_end_limit = 23 if time_value[1] == 24 else time_value[1]
    minute_end_limit = 59 if time_value[1] == 24 else 0
    second_end_limit = 59 if time_value[1] == 24 else 0

    start_limit = datetime(
        date.year,
        date.month,
        date.day,
        hour=hour_start_limit,
        minute=minute_start_limit,
        second=second_start_limit,
        tzinfo=timezone.utc,
    )
    end_limit = datetime(
        date.year,
        date.month,
        date.day,
        hour=hour_end_limit,
        minute=minute_end_limit,
        second=second_end_limit,
        tzinfo=timezone.utc,
    )
    return (start_limit, end_limit)


def _define_data_type(data_types: str) -> DataProducts:
        dataproduct = DataProducts.dtec_2_10
        for name_data in DataProducts.__members__:
            if data_types == name_data:
                dataproduct = DataProducts.__members__[name_data]
                break
        return dataproduct

def _add_line(
        site_data: go.Figure, 
        site_name: Site, 
        dataproduct: DataProducts, 
        local_file: str
) -> None:
    site_data_tmp = retrieve_data(local_file, [site_name])
    sat = list(site_data_tmp[site_name].keys())[0]

    vals = site_data_tmp[site_name][sat][dataproduct]
    times = site_data_tmp[site_name][sat][DataProducts.time]

    number_lines = len(site_data.data)

    site_data.add_trace(
        go.Scatter(
            x=times,
            y=vals + SHIFT * number_lines,
            mode="lines",
            name=site_name.upper(),
        )
    )

    _add_value_yaxis(site_data, site_name, number_lines)

def _add_value_yaxis(
        site_data: go.Figure, 
        site_name: Site,
        number_lines: int
) -> None:
    y_tickmode = site_data.layout.yaxis.tickmode
    if y_tickmode is None:
        site_data.layout.yaxis.tickmode = "array"
        site_data.layout.yaxis.tickvals = [SHIFT * number_lines]
        site_data.layout.yaxis.ticktext = [site_name.upper()]
    else:
        yaxis_data = {"tickvals": [], "ticktext": []}
        for i, site in enumerate(site_data.layout.yaxis.ticktext):
            yaxis_data["tickvals"].append(
                site_data.layout.yaxis.tickvals[i]
            )
            yaxis_data["ticktext"].append(site)
        yaxis_data["tickvals"].append(SHIFT * number_lines)
        yaxis_data["ticktext"].append(site_name.upper())
        _update_yaxis(site_data, yaxis_data)

def _update_yaxis(
        site_data: go.Figure,
        yaxis_data: dict[str, list[float | str]]
) -> None:
    site_data.update_layout(
        yaxis=dict(
            tickmode="array",
            tickvals=yaxis_data["tickvals"],
            ticktext=yaxis_data["ticktext"],
        )
    )

def cteate_new_time_slider(site_data: go.Figure, time_value: list[int]):
    time_slider = create_time_slider() 
    time_slider.disabled = True if len(site_data.data) == 0 else False
    time_slider.value = [time_value[0], time_value[1]]

    return time_slider