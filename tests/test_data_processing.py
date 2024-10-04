import pytest
from spitec import *


@pytest.fixture
def mock_hdf5_file(tmp_path):
    test_file = tmp_path / "test_file.h5"
    with h5py.File(test_file, "w") as f:
        site1 = f.create_group("Site1")
        site2 = f.create_group("Site2")

        sat1 = site1.create_group("Sat1")
        sat1[DataProducts.timestamp.hdf_name] = [1609459200, 1609462800] 
        sat1[DataProducts.dtec_2_10.hdf_name] = [1.0, 2.0] 
        sat1[DataProducts.azimuth.hdf_name] = [0.01, -0.13] 
        sat1[DataProducts.elevation.hdf_name] = [1.2, -5.67] 

        sat2 = site1.create_group("Sat2")
        sat2[DataProducts.timestamp.hdf_name] = [1609459200, 1609462800]
        sat2[DataProducts.dtec_2_10.hdf_name] = [3.0, 4.0]

        sat3 = site2.create_group("Sat3")
        sat3[DataProducts.timestamp.hdf_name] = [1609459200, 1609462800]
        sat3[DataProducts.dtec_2_10.hdf_name] = [5.0, 6.0]

        sat4 = site2.create_group("Sat1")
        sat4[DataProducts.timestamp.hdf_name] = [1609459200, 1609462800]
        sat4[DataProducts.dtec_2_10.hdf_name] = [8.0, 14.0]
        sat4[DataProducts.azimuth.hdf_name] = [-3.6, -5.9] 
        sat4[DataProducts.elevation.hdf_name] = [12, 1.54] 

    yield test_file
    test_file.unlink()

def test_get_satellites(mock_hdf5_file):
    satellites = get_satellites(mock_hdf5_file)

    assert isinstance(satellites, np.ndarray)
    assert satellites.shape == (3,)  
    assert np.all(np.isin(satellites, ["Sat1", "Sat2", "Sat3"]))

def test_retrieve_data(mock_hdf5_file):
    sites = ["Site1", "Site2"]
    sat = "Sat1"
    dataproduct = DataProducts.dtec_2_10

    data, is_satellite = retrieve_data(mock_hdf5_file, sites, Sat(sat), dataproduct)

    assert isinstance(data, dict)
    assert isinstance(is_satellite, dict)
    assert len(data) == 2
    assert len(is_satellite) == 2

    assert "Site1" in data
    assert is_satellite["Site1"] == True
    assert "Sat1" in data["Site1"]
    np.testing.assert_array_equal(data["Site1"][Sat(sat)][dataproduct], np.array([1.0, 2.0]))

    assert "Site2" in data
    assert is_satellite["Site2"] == False 

def test_retrieve_data_missing_site(mock_hdf5_file):
    sites = ["Site1", "UnknownSite"]
    sat = "Sat1"
    dataproduct = DataProducts.dtec_2_10

    data, is_satellite = retrieve_data(mock_hdf5_file, sites, Sat(sat), dataproduct)

    assert isinstance(data, dict)
    assert isinstance(is_satellite, dict)
    assert len(data) == 1  
    assert len(is_satellite) == 1
    assert "Site1" in data
    assert "UnknownSite" not in data
    assert is_satellite["Site1"] == True

def test_retrieve_data_missing_satellite(mock_hdf5_file):
    sites = ["Site2"]
    sat = "UnknownSatellite"
    dataproduct = DataProducts.dtec_2_10

    data, is_satellite = retrieve_data(mock_hdf5_file, sites, Sat(sat), dataproduct)

    assert isinstance(data, dict)
    assert isinstance(is_satellite, dict)
    assert len(data) == 1
    assert len(is_satellite) == 1
    assert "Site2" in data
    assert is_satellite["Site2"] == False 

def test_get_el_az(mock_hdf5_file):
    sites = ["Site1", "Site2"]
    sat = "Sat1"
    site_azimuth, site_elevation, is_satellite = get_el_az(mock_hdf5_file, sites, sat)

    print(is_satellite)
    assert is_satellite[sites[0]] == True and is_satellite[sites[1]] == True
    assert isinstance(site_azimuth, dict) and isinstance(site_elevation, dict)
    assert len(site_azimuth) != 0 
    assert len(site_elevation) != 0 

    np.testing.assert_array_equal(site_azimuth[sites[0]][sat][DataProducts.azimuth], np.array([0.01, -0.13]))
    np.testing.assert_array_equal(site_azimuth[sites[1]][sat][DataProducts.azimuth], np.array([-3.6, -5.9]))
    np.testing.assert_array_equal(site_elevation[sites[0]][sat][DataProducts.elevation], np.array([1.2, -5.67]))
    np.testing.assert_array_equal(site_elevation[sites[1]][sat][DataProducts.elevation], np.array([12, 1.54]))