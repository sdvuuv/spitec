from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from spitec.view.visualization import (
    create_site_map_with_points,
    create_fig_for_map,
    create_site_map_with_tag,
    create_site_map_with_trajectories,
    create_site_data,
    PointColor,
    ProjectionType,
)
from spitec.processing.data_processing import (
    get_namelatlon_arrays,
    get_el_az,
    retrieve_data,
)
from spitec.processing.data_products import DataProducts 
from spitec.processing.trajectorie import Trajectorie
from spitec.processing.site_processing import (
    Site,
    Coordinate,
    Sat,
)



def create_map_with_points(
    site_coords: Optional[dict[Site, dict[Coordinate, float]]],
    projection_value: ProjectionType,
    show_names_site: bool,
    region_site_names: Optional[dict[str, int]],
    site_data_store: Optional[dict[str, int]],
    relayout_data: Optional[dict[str, float]],
    scale_map_store: float,
    new_points: Optional[dict[str, dict[str, str | float]]],
) -> go.Figure:
    """Создает или обновляет карту с точками станций."""
    site_map_points = create_site_map_with_points()
    site_map = create_fig_for_map(site_map_points)

    if projection_value != site_map.layout.geo.projection.type:
        site_map.update_layout(geo=dict(projection_type=projection_value))

    if site_coords is not None:
        site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

        configure_show_site_names(
            show_names_site, site_data_store, site_map, site_array
        )

        colors = np.array(
            [PointColor.SILVER.value] * site_array.shape[0]
        )

        site_map.data[0].lat = lat_array
        site_map.data[0].lon = lon_array
        site_map.data[0].marker.color = colors

        _change_points_color_on_map(
            region_site_names, site_data_store, site_map
        )

        if new_points is not None:
            _add_new_points_to_map(site_map, new_points)

    if relayout_data is not None:
        _change_map_scale_and_center(
            site_map, relayout_data, scale_map_store, projection_value
        )
    return site_map


def _add_new_points_to_map(
    site_map: go.Figure,
    new_points: dict[str, dict[str, str | float]],
) -> None:
    """Добавляет пользовательские точки на карту."""
    for name, value in new_points.items():
        site_map_point = create_site_map_with_tag(
            size=10, 
            marker_symbol=value["marker"],
            name=name
        )
        site_map_point.lat = [value["lat"]]
        site_map_point.lon = [value["lon"]]
        site_map_point.marker.color = value["color"]
        site_map.add_trace(site_map_point)


def configure_show_site_names(
    show_names_site: bool,
    site_data_store: Optional[dict[str, int]],
    site_map: go.Figure,
    site_array: np.ndarray,
) -> None:
    """Настраивает отображение имен станций на карте."""
    sites_to_display_names = []
    if site_data_store:
        sites_to_display_names = list(site_data_store.keys())

    if show_names_site:
        site_map.data[0].text = [site.upper() for site in site_array]
    else:
        site_map.data[0].text = [
            site.upper() if site in sites_to_display_names else ""
            for site in site_array
        ]
        site_map.data[0].customdata = [
            site.upper() if site not in sites_to_display_names else ""
            for site in site_array
        ]
        site_map.data[0].hoverinfo = "text"
        site_map.data[0].hovertemplate = (
            "%{customdata} (%{lat}, %{lon})<extra></extra>"
        )


def _change_map_scale_and_center(
    site_map: go.Figure,
    relayout_data: dict[str, float],
    scale_map_store: float,
    projection_value: ProjectionType,
) -> None:
    """Изменяет масштаб и центр карты."""
    scale = relayout_data.get("geo.projection.scale", scale_map_store)
    
    common_params = dict(
        projection=dict(
            rotation=dict(
                lon=relayout_data.get("geo.projection.rotation.lon", 0)
            ),
            scale=scale,
        ),
        center=dict(
            lon=relayout_data.get("geo.center.lon", 0),
            lat=relayout_data.get("geo.center.lat", 0),
        ),
    )

    if projection_value != ProjectionType.ORTHOGRAPHIC.value:
        site_map.update_layout(geo=common_params)
    else:
        ortho_params = dict(
            projection=dict(
                rotation=dict(
                    lon=relayout_data.get("geo.projection.rotation.lon", 0),
                    lat=relayout_data.get("geo.projection.rotation.lat", 0),
                ),
                scale=scale,
            )
        )
        site_map.update_layout(geo=ortho_params)


def _change_points_color_on_map(
    region_site_names: Optional[dict[str, int]],
    site_data_store: Optional[dict[str, int]],
    site_map: go.Figure,
) -> None:
    """Изменяет цвета точек на карте в зависимости от их статуса."""
    colors = site_map.data[0].marker.color.copy()

    if region_site_names:
        for idx in region_site_names.values():
            colors[idx] = PointColor.GREEN.value
    if site_data_store:
        for idx in site_data_store.values():
            colors[idx] = PointColor.RED.value
    site_map.data[0].marker.color = colors


def _get_trajectory_objects(
    processed_file_path: Path,
    selected_sites_data: dict[str, int],
    site_coordinates: dict[Site, dict[Coordinate, float]],
    satellite: Sat,
    height_m: float,
) -> list[Trajectorie]:
    """Подготавливает список объектов Trajectorie для выбранных станций."""
    trajectory_objects: list[Trajectorie] = []
    _, lat_array, lon_array = get_namelatlon_arrays(site_coordinates)

    for name, idx in selected_sites_data.items():
        traj = Trajectorie(
            name,
            satellite,
            np.radians(lat_array[idx]),
            np.radians(lon_array[idx])
        )
        trajectory_objects.append(traj)

    site_names_list = list(selected_sites_data.keys())
    site_azimuth, site_elevation, is_satellite_data_available = get_el_az(
        processed_file_path, site_names_list, satellite
    )

    for traj in trajectory_objects:
        if not is_satellite_data_available.get(traj.site_name, False):
            traj.sat_exist = False
            continue
        
        az_data = site_azimuth.get(traj.site_name, {}).get(traj.sat_name, {})
        el_data = site_elevation.get(traj.site_name, {}).get(traj.sat_name, {})

        if not (az_data and el_data):
            traj.sat_exist = False
            continue

        traj.add_trajectory_points(
            az_data[DataProducts.azimuth],
            el_data[DataProducts.elevation],
            az_data[DataProducts.time],
            height_m,
        )
    return trajectory_objects


def _find_time_index(
    times_array: np.ndarray,
    target_time: datetime,
    find_later_time: bool = True,
) -> tuple[int, bool]:
    """Находит индекс точного или ближайшего времени в массиве."""
    exact_match_indices = np.where(times_array == target_time)[0]
    is_exact_match = False

    if exact_match_indices.size > 0:
        is_exact_match = True
        return exact_match_indices[0], is_exact_match

    if find_later_time:
        candidate_times_indices = np.where(times_array > target_time)[0]
        if candidate_times_indices.size > 0:
            return candidate_times_indices[0], is_exact_match
    else:
        candidate_times_indices = np.where(times_array < target_time)[0]
        if candidate_times_indices.size > 0:
            return candidate_times_indices[-1], is_exact_match
            
    return -1, is_exact_match 


def create_map_with_trajectories(
    site_map: go.Figure,
    processed_file: Optional[str],
    selected_sites_data: Optional[dict[str, int]],
    site_coordinates: Optional[dict[Site, dict[Coordinate, float]]],
    satellite: Optional[Sat],
    trajectory_colors: dict[Site, str], 
    time_range_hours: list[int], 
    height_m: Optional[float],
    current_sip_tag_time: Optional[dict],
    all_selected_sip_tags: Optional[list[dict]],
    new_manual_trajectories: Optional[dict[str, dict[str, float | str]]],
) -> go.Figure:
    """Добавляет траектории и SIP-теги на карту."""
    if not all([
        satellite, processed_file, site_coordinates, 
        selected_sites_data, height_m
    ]) or not selected_sites_data:
        return site_map
    
    if site_map.layout.geo.projection.type != ProjectionType.ORTHOGRAPHIC.value:
        return site_map 

    processed_file_path = Path(processed_file)

    manual_traj_objs, manual_traj_colors = _get_manual_trajectory_objects(
        new_manual_trajectories
    )
    
    station_traj_objs = _get_trajectory_objects(
        processed_file_path,
        selected_sites_data,
        site_coordinates,
        satellite,
        height_m,
    )
    
    time_limit_start, time_limit_end = _create_datetime_limits_for_xaxis(
        time_range_hours, processed_file_path
    )

    all_trajectory_objects = manual_traj_objs + station_traj_objs
    
    num_manual_trajectories = len(manual_traj_objs)

    for i, traj in enumerate(all_trajectory_objects):
        if not traj.sat_exist:
            continue
        
        current_color: str
        if traj.site_name in trajectory_colors:
            current_color = trajectory_colors[traj.site_name]
        elif i < num_manual_trajectories: 
            current_color = manual_traj_colors[i]
        else:
            current_color = "black" # Цвет по умолчанию
        
        traj.idx_start_point, _ = _find_time_index(traj.times, time_limit_start)
        traj.idx_end_point, _ = _find_time_index(
            traj.times, time_limit_end, find_later_time=False
        )

        if traj.idx_start_point != -1 and traj.traj_lat[traj.idx_start_point] is None:
            traj.idx_start_point += 3
        if traj.idx_end_point != -1 and traj.traj_lat[traj.idx_end_point] is None:
            traj.idx_end_point -= 3

        if (traj.idx_start_point == -1 or 
            traj.idx_end_point == -1 or
            traj.idx_start_point >= traj.idx_end_point):
            continue 

        map_trajectory_trace, map_end_trace = _create_trajectory_traces(
            current_color, traj, traj.site_name
        )
        site_map.add_traces([map_trajectory_trace, map_end_trace])

    should_add_sip_tags = (
        current_sip_tag_time is not None and
        current_sip_tag_time.get("time") and
        (len(current_sip_tag_time["time"]) in [8, 19])
    ) or (all_selected_sip_tags is not None)

    if should_add_sip_tags:
        site_map = _add_sip_tags_to_map(
            site_map=site_map,
            processed_file_path=processed_file_path,
            station_trajectory_objects=station_traj_objs, 
            trajectory_colors=trajectory_colors,
            all_selected_sip_tags=all_selected_sip_tags,
            current_sip_tag_time=current_sip_tag_time,
        )
    return site_map


def _get_manual_trajectory_objects(
    new_trajectory_data: Optional[dict[str, dict[str, float | str]]],
) -> tuple[list[Trajectorie], list[str]]:
    """Создает объекты Trajectorie из данных ручного ввода."""
    manual_trajectory_objects = []
    manual_trajectory_colors = []
    if new_trajectory_data is None:
        return manual_trajectory_objects, manual_trajectory_colors

    for name, data in new_trajectory_data.items():
        trajectory = Trajectorie(name, None, None, None) 
        datetime_array = pd.to_datetime(data["times"])
        trajectory.times = np.array(datetime_array)
        trajectory.traj_lat = np.array(data["traj_lat"], dtype=object)
        trajectory.traj_lon = np.array(data["traj_lon"], dtype=object)
        trajectory.traj_hm = np.array(data["traj_hm"], dtype=object)
        trajectory.sat_exist = True 
        manual_trajectory_colors.append(str(data["color"]))
        manual_trajectory_objects.append(trajectory)
    return manual_trajectory_objects, manual_trajectory_colors


def _create_trajectory_traces(
    color: str,
    trajectory: Trajectorie,
    name: Optional[str] = None,
) -> tuple[go.Scattergeo, go.Scattergeo]:
    """Создает графические объекты Plotly для траектории и ее конца."""
    trajectory_trace = create_site_map_with_trajectories()
    trajectory_trace.lat = trajectory.traj_lat[
        trajectory.idx_start_point:trajectory.idx_end_point:3
    ]
    trajectory_trace.lon = trajectory.traj_lon[
        trajectory.idx_start_point:trajectory.idx_end_point:3
    ]
    trajectory_trace.marker.color = color

    end_point_trace = create_site_map_with_tag(name=name)
    end_point_trace.lat = [trajectory.traj_lat[trajectory.idx_end_point]]
    end_point_trace.lon = [trajectory.traj_lon[trajectory.idx_end_point]]
    end_point_trace.marker.color = color

    return trajectory_trace, end_point_trace


def _add_sip_tags_to_map(
    site_map: go.Figure,
    processed_file_path: Path,
    station_trajectory_objects: list[Trajectorie],
    trajectory_colors: dict[Site, str],
    all_selected_sip_tags: Optional[list[dict]],
    current_sip_tag_time: Optional[dict],
) -> go.Figure:
    active_sip_tags = []
    if all_selected_sip_tags:
        active_sip_tags.extend(all_selected_sip_tags)

    if current_sip_tag_time and current_sip_tag_time.get("time"):
        time_str = current_sip_tag_time["time"]
        if len(time_str) == 8:
            current_date_str = processed_file_path.stem 
            current_sip_tag_time["time"] = f"{current_date_str} {time_str}"
        current_sip_tag_time["coords"] = [] 
        active_sip_tags.append(current_sip_tag_time)

    for i, sip_data in enumerate(active_sip_tags):
        tag_lats: list[Optional[float]] = []
        tag_lons: list[Optional[float]] = []
        tag_point_colors: list[str] = [] 

        target_datetime = convert_str_to_datetime(str(sip_data["time"]))

        for traj in station_trajectory_objects:
            if not traj.sat_exist:
                continue

            sip_tag_idx, is_exact_match = _find_time_index(
                traj.times, target_datetime
            )
            
            valid_start = traj.idx_start_point != -1
            valid_end = traj.idx_end_point != -1

            if is_exact_match and sip_tag_idx != -1 and \
               traj.traj_lat[sip_tag_idx] is not None and \
               traj.traj_lon[sip_tag_idx] is not None and \
               (not valid_start or sip_tag_idx >= traj.idx_start_point) and \
               (not valid_end or sip_tag_idx <= traj.idx_end_point):
                
                lat_rad = np.radians(traj.traj_lat[sip_tag_idx])
                lon_rad = np.radians(traj.traj_lon[sip_tag_idx])

                tag_lats.append(traj.traj_lat[sip_tag_idx])
                tag_lons.append(traj.traj_lon[sip_tag_idx])

                if all_selected_sip_tags and i < len(all_selected_sip_tags) and \
                   all_selected_sip_tags[i].get("site") == traj.site_name:
                    all_selected_sip_tags[i]["lat"] = lat_rad
                    all_selected_sip_tags[i]["lon"] = lon_rad
                
                if current_sip_tag_time and sip_data is current_sip_tag_time:
                     current_sip_tag_time["coords"].append({
                        "site": traj.site_name,
                        "lat": lat_rad,
                        "lon": lon_rad,
                    })

                if sip_data.get("color"): 
                    tag_point_colors.append(str(sip_data["color"]))
                elif traj.site_name in trajectory_colors: 
                    tag_point_colors.append(trajectory_colors[traj.site_name])
                else:
                    tag_point_colors.append("purple") 

        if tag_lats: 
            map_sip_tags_trace = create_site_map_with_tag(
                size=10, 
                marker_symbol=sip_data["marker"],
                name=sip_data["name"],
            )
            map_sip_tags_trace.lat = tag_lats
            map_sip_tags_trace.lon = tag_lons
            if len(set(tag_point_colors)) == 1:
                 map_sip_tags_trace.marker.color = tag_point_colors[0]
            else:
                 map_sip_tags_trace.marker.color = tag_point_colors

            site_map.add_trace(map_sip_tags_trace)
            
    return site_map


def create_site_data_plot_with_values(
    selected_sites_data: Optional[dict[str, int]],
    satellite: Optional[Sat],
    data_type_name: str,
    processed_file: Optional[str],
    time_range_hours: list[int],
    y_axis_shift_value: Optional[float],
    current_sip_tag_time: Optional[dict],
    all_selected_sip_tags: Optional[list[dict]],
) -> go.Figure:
    """Создает график данных со станций"""
    site_data_plot = create_site_data() 

    if not selected_sites_data or not processed_file:
        return site_data_plot

    processed_file_path = Path(processed_file)

    if (current_sip_tag_time and 
        current_sip_tag_time.get("time") and
        len(current_sip_tag_time["time"]) in [8, 19]):
        
        time_str = current_sip_tag_time["time"]
        if len(time_str) == 8:
            current_date_str = processed_file_path.stem
            sip_datetime_str = f"{current_date_str} {time_str}"
        else:
            sip_datetime_str = time_str
        
        sip_tag_dt = convert_str_to_datetime(sip_datetime_str)
        add_vertical_line_to_plot(site_data_plot, sip_tag_dt)

    if all_selected_sip_tags:
        for tag_data in all_selected_sip_tags:
            tag_dt = convert_str_to_datetime(str(tag_data["time"]))
            add_vertical_line_to_plot(
                site_data_plot, tag_dt, str(tag_data.get("color"))
            )
    
    target_data_product = _get_data_product_enum(data_type_name)
    
    if y_axis_shift_value is None or y_axis_shift_value == 0:
        y_axis_shift = -1.0 
        if target_data_product in [
            DataProducts.dtec_2_10, DataProducts.roti, DataProducts.dtec_10_20
        ]:
            y_axis_shift = -0.5
    else:
        y_axis_shift = y_axis_shift_value
        
    _add_data_lines_to_plot(
        site_data_plot,
        list(selected_sites_data.keys()),
        satellite,
        target_data_product,
        processed_file_path,
        y_axis_shift,
    )
    
    if site_data_plot.data: 
        time_limit_start, time_limit_end = _create_datetime_limits_for_xaxis(
            time_range_hours, processed_file_path
        )
        site_data_plot.update_layout(
            xaxis=dict(range=[time_limit_start, time_limit_end])
        )
    return site_data_plot


def add_vertical_line_to_plot(
    plot_figure: go.Figure,
    datetime_value: datetime,
    line_color: str = "darkblue",
) -> None:
    """Добавляет вертикальную линию на график в указанное время."""
    plot_figure.add_shape(
        type="line",
        x0=datetime_value,
        x1=datetime_value,
        y0=0,
        y1=1,
        yref="paper", # Относительно высоты графика
        line=dict(
            color=line_color,
            width=1,
            dash="dash",
        ),
    )


def convert_str_to_datetime(datetime_str: str) -> datetime:
    """Конвертирует строку времени в объект datetime с UTC."""
    # Поддерживает форматы "ГГГГ-ММ-ДД ЧЧ:ММ:СС" и "ЧЧ:ММ:СС" (добавляя текущую дату)
    try:
        dt_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"Invalid datetime format: {datetime_str}")

    return dt_object.replace(tzinfo=timezone.utc)


def _get_data_product_enum(data_product_name: str) -> DataProducts:
    """Возвращает член Enum DataProducts по его имени."""
    try:
        return DataProducts[data_product_name]
    except KeyError:
        # Возвращаем значение по умолчанию или вызываем ошибку,
        return DataProducts.dtec_2_10


def _add_data_lines_to_plot(
    plot_figure: go.Figure,
    site_names: list[Site], 
    satellite: Optional[Sat],
    data_product: DataProducts,
    processed_file_path: Path,
    y_axis_shift: float,
) -> None:
    """Добавляет линии данных (например, TEC) для каждой станции на график."""
    color_palette = px.colors.qualitative.Plotly
    
    site_names_str = [str(name) for name in site_names]

    processed_data, is_satellite_available = retrieve_data(
        processed_file_path, site_names_str, satellite, data_product
    )
    
    scatter_traces = []
    for i, site_name_str in enumerate(site_names_str):
        if satellite is None or not is_satellite_available.get(site_name_str, False):
            if site_name_str not in processed_data or not processed_data[site_name_str]:
                continue 
            
            first_available_sat = list(processed_data[site_name_str].keys())[0]
            data_values = processed_data[site_name_str][first_available_sat][data_product]
            time_values = processed_data[site_name_str][first_available_sat][DataProducts.time]
            # Отображаем как нулевые значения серой линией
            display_values = np.zeros_like(data_values)
            marker_color = "gray"
            marker_size = 2
        else: # Данные по указанному спутнику есть
            # Конвертация в градусы, если это углы
            if data_product in [DataProducts.azimuth, DataProducts.elevation]:
                data_values = np.degrees(
                    processed_data[site_name_str][satellite.name][data_product]
                )
            else:
                data_values = processed_data[site_name_str][satellite.name][data_product]

            time_values = processed_data[site_name_str][satellite.name][DataProducts.time]
            display_values = data_values
            marker_color = color_palette[i % len(color_palette)]
            marker_size = 3

        scatter_traces.append(
            go.Scatter(
                x=time_values,
                y=display_values + y_axis_shift * (i + 1),
                customdata=display_values,
                mode="markers",
                name=site_name_str.upper(),
                hoverinfo="text",
                hovertemplate="%{x}, %{customdata:.2f}<extra></extra>",
                marker=dict(
                    size=marker_size,
                    color=marker_color,
                ),
            )
        )
    plot_figure.add_traces(scatter_traces)

    # Настройка оси Y для отображения имен станций
    plot_figure.layout.yaxis.tickmode = "array"
    plot_figure.layout.yaxis.tickvals = [
        y_axis_shift * (i + 1) for i in range(len(site_names_str))
    ]
    plot_figure.layout.yaxis.ticktext = [name.upper() for name in site_names_str]


def _create_datetime_limits_for_xaxis(
    time_range_hours: list[int],
    processed_file_path: Path,
) -> tuple[datetime, datetime]:
    """Создает начальную и конечную метки времени для оси X."""
    date_str = processed_file_path.stem  
    base_date = datetime.strptime(date_str, '%Y-%m-%d')

    start_hour_val = time_range_hours[0]
    end_hour_val = time_range_hours[1]

    # Обработка случая, когда час указан как 24 (конец дня)
    start_hour = 23 if start_hour_val == 24 else start_hour_val
    start_minute = 59 if start_hour_val == 24 else 0
    start_second = 59 if start_hour_val == 24 else 0
    
    end_hour = 23 if end_hour_val == 24 else end_hour_val
    end_minute = 59 if end_hour_val == 24 else 0
    end_second = 59 if end_hour_val == 24 else 0
    

    start_limit = datetime(
        base_date.year, base_date.month, base_date.day,
        hour=start_hour, minute=start_minute, second=start_second,
        tzinfo=timezone.utc,
    )
    end_limit = datetime(
        base_date.year, base_date.month, base_date.day,
        hour=end_hour, minute=end_minute, second=end_second,
        tzinfo=timezone.utc,
    )

    return start_limit, end_limit