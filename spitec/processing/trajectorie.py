from spitec.processing.site_processing import Site
from spitec.processing.data_processing import Sat
import numpy as np
from datetime import timedelta
from numpy import sin, cos, arcsin, pi

RE_km = 6371

def sub_ionospheric(s_lat, s_lon, hm, az, el, R=RE_km):
    """
    Calculates subionospheric point and delatas from site
    Parameters:
        s_lat, slon - site latitude and longitude in radians
        hm - ionposheric maximum height (km)
        az, el - azimuth and elevation of the site-sattelite line of sight in
            radians
        R - Earth radius (km)
    """
    #TODO use meters
    psi = pi / 2 - el - arcsin(cos(el) * R / (R + hm))
    lat = bi = arcsin(sin(s_lat) * cos(psi) + cos(s_lat) * sin(psi) * cos(az))
    lon = sli = s_lon + arcsin(sin(psi) * sin(az) / cos(bi))

    lon = lon - 2 * pi if lon > pi else lon
    lon = lon + 2 * pi if lon < -pi else lon
    return lat, lon


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
        self.traj_hm = []

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

        self.traj_lat = np.degrees(self.traj_lat)
        self.traj_lon = np.degrees(self.traj_lon)
        self.traj_lat = np.array(self.traj_lat, dtype=object)
        self.traj_lon = np.array(self.traj_lon, dtype=object)

        self.adding_artificial_value()

        assert len(self.traj_lat) == len(self.traj_lon) == len(self.times)

        self.idx_start_point = 0
        self.idx_end_point = len(self.traj_lon) - 1 if len(self.traj_lat) != 0 else 0

 
    def adding_artificial_value(self, minutes: int = 10) -> None:
        # Добавлеем в lat и lon значение None там, где разрыв во времени больше minutes мин
        interval = timedelta(minutes=minutes)
        diffs = np.diff(self.times)
        # Ищем индексы
        indices_to_insert = np.where(diffs > interval)[0] + 1

        # Вставляем среднее время между большими интервалами 
        values_to_insert_time = []
        for i in indices_to_insert:
            midpoint = self.times[i - 1] + (self.times[i] - self.times[i - 1]) / 2
            values_to_insert_time.extend([midpoint - timedelta(seconds=30), midpoint, midpoint + timedelta(seconds=30)])
        values_to_insert_coords = [None] * (3 * len(indices_to_insert))

        # Вставка новых значений в массив
        self.times = np.insert(self.times, indices_to_insert.repeat(3), values_to_insert_time)
        self.traj_lat = np.insert(self.traj_lat, indices_to_insert.repeat(3), values_to_insert_coords)
        self.traj_lon = np.insert(self.traj_lon, indices_to_insert.repeat(3), values_to_insert_coords) 
        if len(self.traj_hm) != 0:
             self.traj_hm = np.insert(self.traj_hm, indices_to_insert.repeat(3), values_to_insert_coords) 