from typing import NamedTuple
from enum import Enum

DataProduct = NamedTuple(
    "DataProduct",
    [
        ("long_name", str),
        ("hdf_name", str),
    ],
)


class DataProducts(DataProduct, Enum):
    roti = DataProduct(
        "ROTI",
        "roti",
    )
    dtec_2_10 = DataProduct(
        "2-10 minute TEC variations",
        "dtec_2_10",
    )
    dtec_10_20 = DataProduct(
        "10-20 minute TEC variations",
        "dtec_10_20",
    )
    dtec_20_60 = DataProduct(
        "20-60 minute TEC variations",
        "dtec_20_60",
    )
    tec = DataProduct(
        "Vertical TEC adjusted using GIM",
        "tec",
    )
    elevation = DataProduct(
        "Elevation angle",
        "elevation",
    )
    azimuth = DataProduct(
        "Azimuth angle",
        "azimuth",
    )
    timestamp = DataProduct(
        "Timestamp",
        "timestamp",
    )
    time = DataProduct("Time (datetime)", None)
