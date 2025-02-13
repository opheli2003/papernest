from app.utils import lambert93_to_gps, load_coverage_data


def test_lambert93_to_gps():
    x = 67000
    y = 55100
    lon, lat = lambert93_to_gps(x, y)
    assert isinstance(lon, float)
    assert not isinstance(lat, int)
    assert lon is not None and lat is not None


def test_load_coverage_data(tmp_path):
    temp_file = tmp_path / "coverage_datas.csv"
    temp_file.write_text("Operateur,x,y,2G,3G,4G\nOrange,67000,55100,1,0,1\n")
    data = load_coverage_data(str(temp_file))
    assert not data.empty
    assert "lon" in data.columns
    assert "lat" in data.columns
    assert "Operateur" in data.columns