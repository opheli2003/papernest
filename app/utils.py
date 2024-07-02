import pyproj
from pyproj import Transformer
import pandas as pd


def lambert93_to_gps(x, y):
    transformer = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lon, lat


def load_coverage_data(filepath):
    data = pd.read_csv(filepath, delimiter=',')
    print('reading it')
    # lecture du fichier CDV
    data[['lon', 'lat']] = data.apply(lambda row: lambert93_to_gps(row['x'], row['y']), axis=1, result_type='expand')
    # stockage des coord GPS (lon, lat) ds de nouvelles colonnes
    return data