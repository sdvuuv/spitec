from spitec.view.visualization import *
from spitec.processing.data_processing import *
from spitec.processing.data_products import DataProducts
from spitec.processing.trajectorie import Trajectorie
from spitec.processing.site_processing import *
from datetime import datetime, timezone
import numpy as np
import plotly.express as px
from pathlib import Path
import pandas as pd


def create_map_with_points(
    site_coords: dict[Site, dict[Coordinate, float]],
    projection_value: ProjectionType,
    show_names_site: bool,
    region_site_names: dict[str, int],
    site_data_store: dict[str, int],
    relayout_data: dict[str, float],
    scale_map_store: float,
    new_points: dict[str, dict[str, str | float]],
) -> go.Figure:
    site_map_points = create_site_map_with_points()
    site_map = create_fig_for_map(site_map_points)

    # Смена проекции
    if projection_value != site_map.layout.geo.projection.type:
        site_map.update_layout(geo=dict(projection_type=projection_value))

    if site_coords is not None:
        site_array, lat_array, lon_array = get_namelatlon_arrays(site_coords)

        # Показать\скрыть имена станций
        configure_show_site_names(show_names_site, site_data_store, site_map, site_array)

        colors = np.array([PointColor.SILVER.value] * site_array.shape[0])

        # Добавление данных
        site_map.data[0].lat = lat_array
        site_map.data[0].lon = lon_array
        site_map.data[0].marker.color = colors

        # Смена цвета точек
        _change_points_on_map(region_site_names, site_data_store, site_map)

        # Добавление точек пользователя
        if new_points is not None:
            _add_new_points(site_map, new_points)
    # Смена маштаба
    if relayout_data is not None:
        _change_scale_map(
            site_map, relayout_data, scale_map_store, projection_value
        )
    return site_map

def _add_new_points(
        site_map: go.Figure,
        new_points: dict[str, dict[str, str | float]],
) -> None:
    for name, value in new_points.items():
        # Создаем объект для отрисовки точек пользователя
        site_map_point = create_site_map_with_tag(10, value["marker"], name) 
        site_map_point.lat = [value["lat"]]
        site_map_point.lon = [value["lon"]]
        site_map_point.marker.color = value["color"]

        # Добавляем на карту
        site_map.add_trace(site_map_point)

def configure_show_site_names(
        show_names_site: bool,
        site_data_store: dict[str, int],
        site_map: go.Figure,
        site_array: NDArray
    ) -> None:
    # Показать\скрыть имена станций
    if show_names_site:
        site_map.data[0].text = [site.upper() for site in site_array]
    else:
        if site_data_store is not None:
            sites_name_lower = list(site_data_store.keys())
        else:
            sites_name_lower = []
        site_map.data[0].text = [
                site.upper() if site in sites_name_lower else ""
                for site in site_array
            ]
        site_map.data[0].customdata = [
                site.upper() if site not in sites_name_lower else ""
                for site in site_array
            ]
        site_map.data[0].hoverinfo = "text"
        site_map.data[0].hovertemplate = (
                "%{customdata} (%{lat}, %{lon})<extra></extra>"
            )

def _change_scale_map(
    site_map: go.Figure,
    relayout_data: dict[str, float],
    scale_map_store: float,
    projection_value: ProjectionType,
) -> None:
    # Меняем маштаб
    if relayout_data.get("geo.projection.scale", None) is not None:
        scale = relayout_data.get("geo.projection.scale")
    else:
        scale = scale_map_store
    if projection_value != ProjectionType.ORTHOGRAPHIC.value:
        site_map.update_layout(
            geo=dict(
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
        )
    else:
        site_map.update_layout(
            geo=dict(
                projection=dict(
                    rotation=dict(
                        lon=relayout_data.get(
                            "geo.projection.rotation.lon", 0
                        ),
                        lat=relayout_data.get(
                            "geo.projection.rotation.lat", 0
                        ),
                    ),
                    scale=scale,
                )
            )
        )

def _change_points_on_map(
    region_site_names: dict[str, int],
    site_data_store: dict[str, int],
    site_map: go.Figure,
) -> None:
    # Меняем цвета точек на карте
    colors = site_map.data[0].marker.color.copy()

    if region_site_names is not None:
        for idx in region_site_names.values():
            colors[idx] = PointColor.GREEN.value
    if site_data_store is not None:
        for idx in site_data_store.values():
            colors[idx] = PointColor.RED.value
    site_map.data[0].marker.color = colors

def _get_objs_trajectories(
        local_file: Path,
        site_data_store: dict[str, int], # все выбранные точки
        site_coords: dict[Site, dict[Coordinate, float]],
        sat: Sat,
        hm: float,
    ) -> list[Trajectorie]:
    list_trajectorie: list[Trajectorie] = []
    _, lat_array, lon_array = get_namelatlon_arrays(site_coords)
    
    # Заполняем список с объектами Trajectorie
    for name, idx in site_data_store.items():
        traj = Trajectorie(name, sat, np.radians(lat_array[idx]), np.radians(lon_array[idx]))
        list_trajectorie.append(traj)
    

    # Извлекаем значения el и az по станциям
    site_names = list(site_data_store.keys())
    site_azimuth, site_elevation, is_satellite = get_el_az(local_file, site_names, sat)
    
    # Добавлем долгату и широту для точек траекторий
    for traj in list_trajectorie:
        if not is_satellite[traj.site_name]:
            traj.sat_exist = False
            continue
        traj.add_trajectory_points(
            site_azimuth[traj.site_name][traj.sat_name][DataProducts.azimuth],
            site_elevation[traj.site_name][traj.sat_name][DataProducts.elevation],
            site_azimuth[traj.site_name][traj.sat_name][DataProducts.time],
            hm
        )
    return list_trajectorie

def _find_time(times: NDArray, target_time: datetime, look_more = True):
    exact_match_idx = np.where(times == target_time)[0]
    exact_time = False

    if exact_match_idx.size > 0:
        # Если точное совпадение найдено
        exact_time = True
        return exact_match_idx[0], exact_time
    else:
        # Если точного совпадения нет, ищем ближайшее большее/меньшее время
        nearest_other_idx = -1
        if look_more:
            other_times = np.where(times > target_time)[0]
            if other_times.size > 0:
                nearest_other_idx = other_times[0]
        else:
            other_times = np.where(times < target_time)[0]
            if other_times.size > 0:
                nearest_other_idx = other_times[-1]

        if nearest_other_idx == -1:
            return -1, exact_time
        
        return nearest_other_idx, exact_time
        

def create_map_with_trajectories(
        site_map: go.Figure,
        local_file: str,
        site_data_store: dict[str, int], # все выбранные точки
        site_coords: dict[Site, dict[Coordinate, float]],
        sat: Sat,
        data_colors: dict[Site, str],
        time_value: list[int],
        hm: float,
        sip_tag_time_dict: dict,
        all_select_sip_tag: list[dict],
        new_trajectory: dict[str, dict[str, float | str]]
) -> go.Figure:
    
    if sat is None or local_file is None or \
        site_coords is None or site_data_store is None or \
            len(site_data_store) == 0 or hm is None or \
                site_map.layout.geo.projection.type != ProjectionType.ORTHOGRAPHIC.value:
        return site_map
    
    local_file_path = Path(local_file)

    new_trajectory_objs, new_trajectory_colors = _get_objs_new_trajectories(
        new_trajectory
    )
    
    # Создаем список с объектом Trajectorie
    trajectory_objs: list[Trajectorie] = _get_objs_trajectories(
        local_file_path, 
        site_data_store, 
        site_coords, 
        sat, 
        hm,
    )
    limit_start, limit_end = _create_limit_xaxis(time_value, local_file_path)

    new_trajectory_objs.extend(trajectory_objs)
    for i, traj in enumerate(new_trajectory_objs):
        if not traj.sat_exist: # данных по спутнику нет
            continue
        
        # Определяем цвет траектории
        if traj.site_name in data_colors.keys(): 
            curtent_color = data_colors[traj.site_name]
        elif i < len(new_trajectory_objs) - len(trajectory_objs):
            curtent_color = new_trajectory_colors[i]
        else:
            curtent_color = "black"
        
        # Ищем ближайщие индексы времени
        traj.idx_start_point, _ = _find_time(traj.times, limit_start)
        traj.idx_end_point, _ = _find_time(traj.times, limit_end, False)
        if traj.traj_lat[traj.idx_start_point] is None:
            traj.idx_start_point += 3
        if traj.traj_lat[traj.idx_end_point] is None:
            traj.idx_end_point -= 3

        if traj.idx_start_point >= traj.idx_end_point or \
            traj.idx_start_point == -1 or \
            traj.idx_end_point == -1:
            # если не нашли, или нашли неверно
            continue

        # создаем объекты для отрисовки траектории
        site_map_trajs, site_map_end_trajs = _create_trajectory(curtent_color, traj, traj.site_name)
        site_map.add_traces([site_map_trajs, site_map_end_trajs])

    if ( sip_tag_time_dict is not None and sip_tag_time_dict["time"] is not None and \
        (len(sip_tag_time_dict["time"]) == 8 or len(sip_tag_time_dict["time"]) == 19) ) or \
        (all_select_sip_tag is not None):
        site_map = _add_sip_tags(
            site_map,
            local_file_path,
            trajectory_objs, 
            data_colors, 
            all_select_sip_tag,
            sip_tag_time_dict
        )
    return site_map

def _get_objs_new_trajectories(
        new_trajectory: dict[str, dict[str, float | str]]
    ) -> list[list[Trajectorie], list[str]]:
    new_trajectory_objs = []
    new_trajectory_colors = []
    if new_trajectory is not None:
        for name, data in new_trajectory.items():
            trajectory = Trajectorie(name, None, None, None)
            datetime_array = pd.to_datetime(data["times"])
            trajectory.times = np.array(datetime_array)
            trajectory.traj_lat = np.array(data["traj_lat"], dtype=object)
            trajectory.traj_lon = np.array(data["traj_lon"], dtype=object)
            trajectory.traj_hm = np.array(data["traj_hm"], dtype=object)
            new_trajectory_colors.append(data["color"])
            new_trajectory_objs.append(trajectory)
    return new_trajectory_objs, new_trajectory_colors

def _create_trajectory(
        current_color: str,
        traj: Trajectorie,
        name: str = None
    ) -> list[go.Scattergeo]:
    site_map_trajs = create_site_map_with_trajectories() # создаем объект для отрисовки траектории
    site_map_end_trajs = create_site_map_with_tag(name=name) # создаем объект для отрисовки конца траектории

    # Устанавливаем точки траектории
    site_map_trajs.lat = traj.traj_lat[traj.idx_start_point:traj.idx_end_point:3]
    site_map_trajs.lon = traj.traj_lon[traj.idx_start_point:traj.idx_end_point:3]
    site_map_trajs.marker.color = current_color

    # Устанавливаем координаты последней точки
    site_map_end_trajs.lat = [traj.traj_lat[traj.idx_end_point]]
    site_map_end_trajs.lon = [traj.traj_lon[traj.idx_end_point]]
    site_map_end_trajs.marker.color = current_color

    return site_map_trajs, site_map_end_trajs

def _add_sip_tags(
        site_map: go.Figure,
        local_file: Path,
        trajectory_objs: list[Trajectorie],
        data_colors: dict[Site, str],
        all_select_st: list[dict],
        sip_tag_time_dict: dict
    ):
    if all_select_st is None:
        all_select_sip_tag = []
    else:
        all_select_sip_tag = all_select_st.copy()

    if sip_tag_time_dict is not None:
        if len(sip_tag_time_dict["time"]) == 8:
            sip_tag_time = sip_tag_time_dict["time"]
            current_date = local_file.stem  # Получаем '2024-01-01'
            sip_tag_time_dict["time"] = f"{current_date} {sip_tag_time}"
        sip_tag_time_dict["coords"] = []
        all_select_sip_tag.append(sip_tag_time_dict)

    for i, sip_data in enumerate(all_select_sip_tag):
        tag_lat = []
        tag_lon = []
        tag_color = []
        for traj in trajectory_objs:
            if not traj.sat_exist: # данных по спутнику нет
                continue

            if isinstance(sip_data["time"], str):
                tag_time = convert_time(sip_data["time"])
            else:
                tag_time = sip_data["time"]

            # получаем индекс метки времени
            sip_tag_idx, exact_time = _find_time(traj.times, tag_time) 

            idx_start_point = traj.idx_start_point
            idx_end_point = traj.idx_end_point
            if idx_start_point == -1:
                idx_start_point = sip_tag_idx + 1

            if idx_end_point == -1:
                idx_end_point = sip_tag_idx - 1

            if exact_time and traj.traj_lat[sip_tag_idx] is not None:
                if sip_tag_idx >= idx_start_point and sip_tag_idx <= idx_end_point:
                    tag_lat.append(traj.traj_lat[sip_tag_idx])
                    tag_lon.append(traj.traj_lon[sip_tag_idx])
                if all_select_st is not None and \
                    i < len(all_select_st) and \
                        all_select_st[i]["site"] == traj.site_name:
                    all_select_st[i]["lat"] = np.radians(traj.traj_lat[sip_tag_idx])
                    all_select_st[i]["lon"] = np.radians(traj.traj_lon[sip_tag_idx])
                
                if sip_tag_time_dict is not None:
                    sip_tag_time_dict["coords"].append({
                        "site": traj.site_name,
                        "lat": np.radians(traj.traj_lat[sip_tag_idx]),
                        "lon": np.radians(traj.traj_lon[sip_tag_idx])
                    }
                ) 

                if sip_data["color"] is None:
                    tag_color.append(data_colors[traj.site_name])
                else:
                    tag_color = sip_data["color"]

        site_map_tags = create_site_map_with_tag(10, sip_data["marker"], sip_data["name"])
        site_map_tags.lat = tag_lat
        site_map_tags.lon = tag_lon
        site_map_tags.marker.color = tag_color
        
        site_map.add_trace(site_map_tags)
    return site_map

def create_site_data_with_values(
    site_data_store: dict[str, int],
    sat: Sat,
    data_types: str,
    local_file: str,
    time_value: list[int],
    shift: float,
    sip_tag_time_dict: dict,
    all_select_sip_tag: list[dict],
) -> go.Figure:
    site_data = create_site_data()
    
    if site_data_store is not None and site_data_store:
        local_file_path = Path(local_file)
        if sip_tag_time_dict is not None and \
            sip_tag_time_dict["time"] is not None and \
                (len(sip_tag_time_dict["time"]) == 8 or len(sip_tag_time_dict["time"]) == 19):
            sip_tag_time = sip_tag_time_dict["time"]
            if len(sip_tag_time) == 8:
                current_date = local_file_path.stem  # Получаем '2024-01-01'
                sip_tag_datetime = datetime.strptime(f"{current_date} {sip_tag_time}", "%Y-%m-%d %H:%M:%S")
            elif len(sip_tag_time) == 19:
                sip_tag_datetime = datetime.strptime(sip_tag_time, "%Y-%m-%d %H:%M:%S")
            sip_tag_datetime = sip_tag_datetime.replace(tzinfo=timezone.utc)
            add_sip_tag_line(site_data, sip_tag_datetime)

        if all_select_sip_tag is not None and len(all_select_sip_tag) != 0:
            for tag in all_select_sip_tag:
                
                if isinstance(tag["time"], str):
                    tag_time = convert_time(tag["time"])
                else:
                    tag_time = tag["time"]

                add_sip_tag_line(site_data, tag_time, tag["color"])
        
        # Определяем тип данных
        dataproduct = _define_data_type(data_types)
        # Определяем размер сдвига
        if shift is None or shift == 0:
            shift = -1
            if dataproduct in [DataProducts.dtec_2_10, DataProducts.roti, DataProducts.dtec_10_20]:
                shift = -0.5
        # Добавляем данные        
        _add_lines(
            site_data,
            list(site_data_store.keys()),
            sat,
            dataproduct,
            local_file_path,
            shift,
        )
        if len(site_data.data) > 0:
            # Ограничиваем вывод данных по времени
            limit = _create_limit_xaxis(time_value, local_file_path) 
            site_data.update_layout(xaxis=dict(range=[limit[0], limit[1]]))
    return site_data

def add_sip_tag_line(
        site_data: go.Figure,
        sip_tag_datetime: datetime,
        color: str = "darkblue"
    ) -> None:
    site_data.add_shape(
        type="line",
        x0=sip_tag_datetime,
        x1=sip_tag_datetime,
        y0=0,
        y1=1,  
        yref="paper",  
        line=dict(
            color=color,  
            width=1,      
            dash="dash" 
        )
    )

def convert_time(point_x: str) -> datetime:
        x_time = datetime.strptime(
            point_x, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        
        return x_time


def _define_data_type(data_types: str) -> DataProducts:
    # Определяем тип данных
    dataproduct = DataProducts.dtec_2_10
    for name_data in DataProducts.__members__:
        if data_types == name_data:
            dataproduct = DataProducts.__members__[name_data]
            break
    return dataproduct


def _add_lines(
    site_data: go.Figure,
    sites_name: list[Site],
    sat: Sat,
    dataproduct: DataProducts,
    local_file: Path,
    shift: float,
) -> None:
    # Получем все возможные цвета
    colors = px.colors.qualitative.Plotly
    # Ивлекаем данные
    site_data_tmp, is_satellite = retrieve_data(
        local_file, sites_name, sat, dataproduct
    )
    scatters = []
    for i, name in enumerate(sites_name):
        if sat is None or not is_satellite[name]: # Если у станции нет спутника
            sat_tmp = list(site_data_tmp[name].keys())[0]

            vals = site_data_tmp[name][sat_tmp][dataproduct]
            times = site_data_tmp[name][sat_tmp][DataProducts.time]
            vals_tmp = np.zeros_like(vals)

            # Рисуем прямую серую линию
            scatters.append(
                go.Scatter(
                    x=times,
                    y=vals_tmp + shift * (i + 1),
                    customdata=vals_tmp,
                    mode="markers",
                    name=name.upper(),
                    hoverinfo="text",
                    hovertemplate="%{x}, %{customdata}<extra></extra>",
                    marker=dict(
                        size=2,
                        color = "gray",
                    ),
                )
            )
        else: # Если у станции есть спутник
            # Если azimuth или elevation переводим в градусы
            if (
                dataproduct == DataProducts.azimuth
                or dataproduct == DataProducts.elevation
            ):
                vals = np.degrees(site_data_tmp[name][sat][dataproduct])
            else:
                vals = site_data_tmp[name][sat][dataproduct]

            times = site_data_tmp[name][sat][DataProducts.time]

            # Определяем цвет данных на графике
            idx_color = i if i < len(colors) else i - len(colors)*(i // len(colors))
            # Рисуем данные
            scatters.append(
                go.Scatter(
                    x=times,
                    y=vals + shift * (i + 1),
                    customdata=vals,
                    mode="markers",
                    name=name.upper(),
                    hoverinfo="text",
                    hovertemplate="%{x}, %{customdata}<extra></extra>",
                    marker=dict(
                        size=3,
                        color = colors[idx_color],
                    ),
                )
            )
    site_data.add_traces(scatters)

    # Настраиваем ось y для отображения имен станций
    site_data.layout.yaxis.tickmode = "array"
    site_data.layout.yaxis.tickvals = [
        shift * (i + 1) for i in range(len(sites_name))
    ]
    site_data.layout.yaxis.ticktext = list(map(str.upper, sites_name))


def _create_limit_xaxis(
    time_value: list[int], local_file: Path
) -> tuple[datetime]:
    # Переводим целые значения времени в datetime
    date = local_file.stem  # Получаем '2024-01-01'
    date = datetime.strptime(date, '%Y-%m-%d')

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