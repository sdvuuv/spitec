from pathlib import Path
import h5py
from enum import Enum
import numpy as np
from numpy.typing import NDArray

class Site(str):
    pass

class Coordinate(Enum):
    lat="latitude"
    lon="longitude"

def get_sites_coords(local_file: str | Path) -> dict[Site, dict[Coordinate, float]]:
    f = h5py.File(local_file)
    sites = list(f.keys())
    coords = dict()
    for site in sites:
        site_info = f[site].attrs
        site_lat = np.degrees(site_info['lat'])
        site_lon = np.degrees(site_info['lon'])

        coords[site] = dict()
        coords[site][Coordinate.lat] = site_lat
        coords[site][Coordinate.lon] = site_lon
    f.close()
    return coords


def get_namelatlon_arrays(
    site_coords: dict[Site, dict[Coordinate, float]]
) -> tuple[NDArray]:
    site_names =  np.array(list(site_coords.keys()))
    latitudes = [site_coords[name][Coordinate.lat] for name in site_names]
    longitudes = [site_coords[name][Coordinate.lon] for name in site_names]

    latitudes_array = np.array(latitudes)
    longitudes_array = np.array(longitudes)
    return site_names, latitudes_array, longitudes_array