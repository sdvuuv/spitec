import h5py
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from numpy.typing import NDArray
from spitec.processing.site_processing import Site 
from spitec.processing.data_products import DataProduct, DataProducts


class Sat(str):
    pass


def retrieve_data(
    local_file: str | Path,
    sites: list[Site],
    sat: Sat,
    dataproduct: DataProducts,
) -> list[dict[Site, dict[Sat, dict[DataProduct, NDArray]]], dict[str, bool]]:
    f = h5py.File(local_file)
    data = dict()
    is_satellite = dict()
    for site in sites:
        if not site in f:
            continue
        data[site] = dict()
        satellites = list(f[site].keys())
        sat_tmp = sat
        if sat is None or sat not in satellites:
            sat_tmp = satellites[0]
            is_satellite[site] = False
        else:
            is_satellite[site] = True
        timestamps = f[site][sat_tmp][DataProducts.timestamp.hdf_name][:]
        times = [datetime.fromtimestamp(t, timezone.utc) for t in timestamps]
        data[site][sat_tmp] = {DataProducts.time: np.array(times)}
        data[site][sat_tmp][dataproduct] = f[site][sat_tmp][
            dataproduct.hdf_name
        ][:]
    f.close()
    return data, is_satellite


def get_el_az(
        local_file: str,
        site_names: list[Site],
        sat
    ) -> list[dict, dict, dict[str, bool]]:
    dataproduct_az = DataProducts.azimuth
    dataproduct_el = DataProducts.elevation

    site_azimuth, is_satellite = retrieve_data(
        local_file, site_names, sat, dataproduct_az
    )
    site_elevation, _ = retrieve_data(
        local_file, site_names, sat, dataproduct_el
    )
    return site_azimuth, site_elevation, is_satellite


def get_satellites(local_file: str | Path) -> NDArray:
    satellites = []
    f = h5py.File(local_file)
    for site in f:
        sats = list(f[site].keys())
        satellites.extend(sats)
    satellites = np.array(satellites)
    satellites = np.unique(satellites)
    f.close()
    return satellites
