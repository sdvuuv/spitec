from pathlib import Path
import h5py
from enum import Enum
import numpy as np
from numpy.typing import NDArray
from numpy import pi, sin, cos, arccos
import requests
import json
import hashlib


DOWNLOAD_URL = "https://simurg.space/gen_file?data=obs&date="
RE_meters = 6371000.0


class Site(str):
    pass


class Coordinate(Enum):
    lat = "latitude"
    lon = "longitude"


def load_data(filename: str, local_file: str | Path):
    url = DOWNLOAD_URL + filename
    max_load_per = 100
    with open(local_file, "wb") as f:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            response.raise_for_status()
        total_length = response.headers.get("content-length")

        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            previous = 0
            total_length = int(total_length)
            for chunk in response.iter_content(chunk_size=4096):
                dl += len(chunk)
                f.write(chunk)
                done = int(max_load_per * dl / total_length)
                if done > previous:
                    yield done
                previous = done
                

def сheck_file_size(filename: str) -> int:
    url = DOWNLOAD_URL + filename
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        return None
    total_length = response.headers.get("content-length")

    if total_length is None:
        return 0
    else:
        Mb = round(float(total_length) / 1024 / 1024 / 1024, 2)
        return Mb
    
def calculate_json_hash(data: dict):
    json_string = json.dumps(data, sort_keys=True).encode('utf-8')

    hash_object = hashlib.sha256()
    hash_object.update(json_string)

    return hash_object.hexdigest()

def save_data_json(file_name: Path | str, data: dict) -> bool:
    try:
        with open(file_name, 'w') as f:
            json.dump(data, f)
        return True
    except ValueError:
        return False

def load_data_json(file_name: Path | str) -> dict:
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def get_sites_coords(
    local_file: str | Path,
) -> dict[Site, dict[Coordinate, float]]:
    f = h5py.File(local_file)
    sites = list(f.keys())
    coords = dict()
    for site in sites:
        site_info = f[site].attrs
        _add_site_to_dict(coords, site, site_info["lat"], site_info["lon"])
    f.close()
    return coords


def get_namelatlon_arrays(
    site_coords: dict[Site, dict[Coordinate, float]]
) -> tuple[NDArray]:
    site_names = np.array(list(site_coords.keys()))
    latitudes = [
        np.degrees(site_coords[name][Coordinate.lat.value]) for name in site_names
    ]
    longitudes = [
        np.degrees(site_coords[name][Coordinate.lon.value]) for name in site_names
    ]

    latitudes_array = np.array(latitudes)
    longitudes_array = np.array(longitudes)
    return site_names, latitudes_array, longitudes_array


def select_sites_by_region(
    coords: dict[Site, dict[Coordinate, float]],
    min_lat: float = -90,
    max_lat: float = 90,
    min_lon: float = -180,
    max_lon: float = 180,
) -> dict[Site, dict[Coordinate, float]]:
    regional_coords = dict()
    sites = list(coords.keys())
    for site in sites:
        site_lat_radians = coords[site][Coordinate.lat.value]
        site_lon_radians = coords[site][Coordinate.lon.value]

        site_lat = np.degrees(site_lat_radians)
        site_lon = np.degrees(site_lon_radians)
        if min_lat < site_lat < max_lat and min_lon < site_lon < max_lon:
            _add_site_to_dict(
                regional_coords, site, site_lat_radians, site_lon_radians
            )
    return regional_coords


def get_great_circle_distance(
    late: NDArray | float,
    lone: NDArray | float,
    latp: NDArray | float,
    lonp: NDArray | float,
    R: float = RE_meters,
) -> float:
    if np.isscalar(lone):
        lone = np.array([lone])
    if np.isscalar(lonp):
        lonp = np.array([lonp])
    lone[np.where(lone < 0)] = lone[np.where(lone < 0)] + 2 * pi
    lonp[np.where(lonp < 0)] = lonp[np.where(lonp < 0)] + 2 * pi
    dlon = lonp - lone
    inds = np.where((dlon > 0) & (dlon > pi))
    dlon[inds] = 2 * pi - dlon[inds]
    dlon[np.where((dlon < 0) & (dlon < -pi))] += 2 * pi
    dlon[np.where((dlon < 0) & (dlon < -pi))] = -dlon[
        np.where((dlon < 0) & (dlon < -pi))
    ]
    cosgamma = sin(late) * sin(latp) + cos(late) * cos(latp) * cos(dlon)
    return R * arccos(cosgamma)


def select_sites_in_circle(
    coords: dict[Site, dict[Coordinate, float]],
    central_point: dict[Coordinate, float],
    distance_threshold: float,
) -> dict[Site, dict[Coordinate, float]]:
    late_central = np.radians(central_point[Coordinate.lat.value])
    lone_central = np.radians(central_point[Coordinate.lon.value])

    circular_coords = dict()
    sites = list(coords.keys())
    for site in sites:
        late = coords[site][Coordinate.lat.value]
        lone = coords[site][Coordinate.lon.value]

        distance = (
            get_great_circle_distance(late, lone, late_central, lone_central)
            / 1000
        )  # км
        if distance <= distance_threshold:
            _add_site_to_dict(circular_coords, site, late, lone)
    return circular_coords


def _add_site_to_dict(
    coords: dict[Site, dict[Coordinate, float]],
    site: Site,
    lat: float,
    lon: float,
) -> None:
    coords[site] = dict()
    coords[site][Coordinate.lat.value] = lat
    coords[site][Coordinate.lon.value] = lon
