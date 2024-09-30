from spitec.processing.site_processing import Site
from spitec.processing.data_processing import Sat
from simurg_core.geospace.sub_ionospheric import sub_ionospheric
import numpy as np

class Trajectorie:
    
    def __init__(
        self, 
        site_name: Site, 
        sat_name: Sat,
        lat_site: float, 
        lon_site: float
    ) -> None:
        self.site_name = site_name
        self.sat_name = sat_name
        self.lat_site = lat_site
        self.lon_site = lon_site
        self.traj_lat = []
        self.traj_lon = []
        self.times = []
        self.idx_start_point = 0
        self.idx_end_point = 0
        self.sat_exist = True

    def add_trajectory_points(self, azs, els, times, hm = 300) -> None:
        self.sat_exist = True
        self.times = times
        for az, el in zip(azs, els):
            # получаем значения широты и долготы по az, el
            lat, lon = sub_ionospheric( 
                self.lat_site,
                self.lon_site,
                hm,
                az,
                el
            )
            self.traj_lat.append(lat)
            self.traj_lon.append(lon)

        self.traj_lat = np.degrees(np.array(self.traj_lat))
        self.traj_lon = np.degrees(np.array(self.traj_lon))

        assert len(self.traj_lat) == len(self.traj_lon)

        self.idx_start_point = 0
        self.idx_end_point = len(self.traj_lon) - 1 if len(self.traj_lat) != 0 else 0