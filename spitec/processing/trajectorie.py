from spitec.processing.site_processing import Site
from spitec.processing.data_processing import Sat
from simurg_core.geospace.sub_ionospheric import sub_ionospheric

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
        self.__idx_start_point = 0
        self.__idx_end_point = 0

    def add_trajectory_points(self, azs, els, hm = 10) -> list[float, float]:
        for az, el in zip(azs, els):
            lat, lon = sub_ionospheric(
                self.lat_site,
                self.lon_site,
                hm,
                az,
                el
            )
            self.traj_lat.append(lat)
            self.traj_lon.append(lon)

    @property
    def idx_start_point(self) -> float:
        return self.idx_start_point
    
    @idx_start_point.setter
    def idx_start_point(self, val: float) -> float:
        self.idx_start_point = val

    @property
    def idx_end_point(self) -> float:
        return self.idx_end_point
    
    @idx_end_point.setter
    def idx_end_point(self, val: float) -> float:
        self.idx_end_point = val