import pytest
import requests
from unittest.mock import MagicMock
from spitec import *

@pytest.fixture
def mock_requests_get(mocker):
    def _mock_requests_get(url, stream=True, status_code=200, content_length=None):
        response = MagicMock()
        response.status_code = status_code
        if status_code == 404:
            response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        if content_length is not None:
            response.headers = {"content-length": str(content_length)}
            response.iter_content = MagicMock(return_value=[b'a' * 4096, b'b' * 4096])
        else:
            response.headers = {}
            response.content = b'abc' * 4096 if status_code == 200 else b''
            response.iter_content = MagicMock(return_value=[])
        return response

    return _mock_requests_get


def test_load_data(mocker, tmp_path, mock_requests_get):
    filename = "testfile"
    local_file = tmp_path / "localfile"

    mocker.patch('requests.get', side_effect=lambda url, stream=True: mock_requests_get(url, stream, content_length=8192))
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    generator = load_data(filename, local_file)

    try:
        for progress in generator:
            assert isinstance(progress, int)
            assert 0 <= progress <= 100
    except StopIteration:
        pass

    mock_open.assert_called_once_with(local_file, "wb")
    handle = mock_open()
    handle.write.assert_any_call(b'a' * 4096)
    handle.write.assert_any_call(b'b' * 4096)

    requests.get.assert_called_once_with(DOWNLOAD_URL + filename, stream=True)

def test_load_data_no_content_length(mocker, tmp_path, mock_requests_get):
    filename = "testfile"
    local_file = tmp_path / "localfile"

    mocker.patch('requests.get', side_effect=lambda url, stream=True: mock_requests_get(url, stream))
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    generator = load_data(filename, local_file)

    with pytest.raises(StopIteration):
        next(generator)

    mock_open.assert_called_once_with(local_file, "wb")
    handle = mock_open()
    handle.write.assert_called_once_with(b'abc' * 4096)

    requests.get.assert_called_once_with(DOWNLOAD_URL + filename, stream=True)

def test_load_data_http_error(mocker, tmp_path, mock_requests_get):
    filename = "testfile"
    local_file = tmp_path / "localfile"

    mocker.patch('requests.get', side_effect=lambda url, stream=True: mock_requests_get(url, stream, status_code=404))
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    with pytest.raises(requests.exceptions.HTTPError):
        list(load_data(filename, local_file))

    requests.get.assert_called_once_with(DOWNLOAD_URL + filename, stream=True)
    mock_open.assert_called_once_with(local_file, "wb")
    mock_open().write.assert_not_called()

    requests.get.assert_called_once_with(DOWNLOAD_URL + filename, stream=True)

def test_check_file_size_success(mocker, mock_requests_get):
    filename = "testfile"
    mocker.patch('requests.get', side_effect=lambda url, stream=True: mock_requests_get(url, stream, content_length=104857600))

    size = сheck_file_size(filename)
    assert size == 0.1  # 100 MB -> 0.1 GB

def test_check_file_size_no_content_length(mocker, mock_requests_get):
    filename = "testfile"
    mocker.patch('requests.get', side_effect=lambda url, stream=True: mock_requests_get(url, stream))

    size = сheck_file_size(filename)
    assert size == 0

def test_check_file_size_http_error(mocker, mock_requests_get):
    filename = "testfile"
    mocker.patch('requests.get', side_effect=lambda url, stream=True: mock_requests_get(url, stream, status_code=404))

    size = сheck_file_size(filename)
    assert size is None


@pytest.fixture
def mock_hdf5_file(tmp_path):
    test_file = tmp_path / "testfile.h5"
    with h5py.File(test_file, "w") as f:
        site1 = f.create_group("Site1")
        site1.attrs["lat"] = 1.0
        site1.attrs["lon"] = 2.0

        site2 = f.create_group("Site2")
        site2.attrs["lat"] = 0.5
        site2.attrs["lon"] = -2.5

    yield test_file
    test_file.unlink()

def test_get_sites_coords(mock_hdf5_file):
    coords = get_sites_coords(mock_hdf5_file)

    assert isinstance(coords, dict)
    assert len(coords) == 2

    assert "Site1" in coords
    assert coords["Site1"][Coordinate.lat.value] == 1.0
    assert coords["Site1"][Coordinate.lon.value] == 2.0

    assert "Site2" in coords
    assert coords["Site2"][Coordinate.lat.value] == 0.5
    assert coords["Site2"][Coordinate.lon.value] == -2.5

    assert all(isinstance(coord, float) for site_coords in coords.values() for coord in site_coords.values())


def test_get_namelatlon_arrays(mock_hdf5_file):
    site_coords = get_sites_coords(mock_hdf5_file)

    site_names, lat_array, lon_array = get_namelatlon_arrays(site_coords)

    assert isinstance(site_names, np.ndarray)
    assert isinstance(lat_array, np.ndarray)
    assert isinstance(lon_array, np.ndarray)

    assert site_names.shape == (2,) 
    assert lat_array.shape == (2,)
    assert lon_array.shape == (2,)

    expected_site_names = np.array(["Site1", "Site2"])
    expected_lat = np.array([57.3, 28.65])
    expected_lon = np.array([114.59, -143.24])

    np.testing.assert_array_equal(site_names, expected_site_names)
    np.testing.assert_array_almost_equal(lat_array, expected_lat, decimal=2)
    np.testing.assert_array_almost_equal(lon_array, expected_lon, decimal=2)


def test_select_sites_by_region(mock_hdf5_file):
    coords = get_sites_coords(mock_hdf5_file)

    regional_coords = select_sites_by_region(coords)
    assert len(regional_coords) == 2 # all sites

    regional_coords = select_sites_by_region(coords, min_lat=40, max_lat=60, min_lon=100, max_lon=180)
    assert len(regional_coords) == 1 # first sites

    regional_coords = select_sites_by_region(coords, min_lat=0, max_lat=40)
    assert len(regional_coords) == 1 # second sites

    regional_coords = select_sites_by_region(coords, min_lat=0, max_lat=10, min_lon=0, max_lon=10)
    assert len(regional_coords) == 0 # no sites


def test_get_great_circle_distance():
    distance = get_great_circle_distance(1.0, 2.0, 0.87, 1.7)
    assert np.isclose(distance, 1398591.68, atol=0.01)

    distances = get_great_circle_distance(np.array([1.0, 0.5]), np.array([2.0, -2.5]), 0.69, 0)
    print(distances)
    assert np.allclose(distances, [7646164.25, 11532417.92], atol=0.01)


def test_select_sites_in_circle(mock_hdf5_file):
    coords = get_sites_coords(mock_hdf5_file)

    central_point = {Coordinate.lat.value: 40.0, Coordinate.lon.value: 0.0}
    distance_threshold = 12000.0
    circular_coords = select_sites_in_circle(coords, central_point, distance_threshold)
    assert len(circular_coords) == 2 # all sites

    distance_threshold = 8000.0
    circular_coords = select_sites_in_circle(coords, central_point, distance_threshold)
    assert len(circular_coords) == 1 # first sites

    central_point = {Coordinate.lat.value: 28.65, Coordinate.lon.value: -143.24}
    distance_threshold = 10.0
    circular_coords = select_sites_in_circle(coords, central_point, distance_threshold)
    assert len(circular_coords) == 1 # second sites

    central_point = {Coordinate.lat.value: 10.0, Coordinate.lon.value: 20.0}
    distance_threshold = 1.0
    circular_coords = select_sites_in_circle(coords, central_point, distance_threshold)
    assert len(circular_coords) == 0 # no sites
