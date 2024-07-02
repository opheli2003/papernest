from app.utils import lambert93_to_gps, load_coverage_data


def test_lambert93_to_gps():
    x = 700000
    y = 6600000
    lon, lat = lambert93_to_gps(x, y)
    assert isinstance(lon, float)
    assert isinstance(lat, float)
    assert lon != 0
    assert lat != 0


def test_load_coverage_data(tmp_path):
    # Créer un fichier CSV de test
    test_csv = tmp_path / "test_coverage.csv"
    test_csv.write_text("x,y,Operateur,2G,3G,4G\n700000,6600000,Operator1,1,1,1\n")

    data = load_coverage_data(test_csv)
    assert not data.empty
    assert "lon" in data.columns
    assert "lat" in data.columns