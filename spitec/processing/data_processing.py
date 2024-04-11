import h5py
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from numpy.typing import NDArray
from .site_processing import Site
from .data_products import DataProduct, DataProducts


class Sat(str):
    pass


def retrieve_data(
    local_file: str | Path,
    sites: list[Site],
) -> dict[Site, dict[Sat, dict[DataProduct, NDArray]]]:
    f = h5py.File(local_file)
    data = dict()
    for site in sites:
        if not site in f:
            continue
        data[site] = dict()
        for sat in f[site].keys():
            timestamps = f[site][sat][DataProducts.timestamp.hdf_name][:]
            times = [datetime.fromtimestamp(t, timezone.utc) for t in timestamps]
            data[site][sat] = {DataProducts.time: np.array(times)}
            for dataproduct in DataProducts:
                if dataproduct is DataProducts.time:
                    continue
                data[site][sat][dataproduct] = f[site][sat][dataproduct.hdf_name][:]
    f.close()
    return data
