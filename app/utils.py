from typing import Tuple

import pyproj
import pandas as pd


def lambert93_to_gps(x: float, y: float) -> Tuple[float, float]:
    transformer = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lon, lat


def load_coverage_data(filepath: str) -> pd.DataFrame:
    data = pd.read_csv(filepath, delimiter=',')
    data[['lon', 'lat']] = data.apply(lambda row: lambert93_to_gps(row['x'], row['y']), axis=1, result_type='expand')
    return data
