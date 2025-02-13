
import logging
import os
from typing import Union

import pyproj
import pandas as pd
from rich.logging import RichHandler

logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])


_transformer = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)


def lambert93_to_gps(x: float, y: float) -> Union[tuple[float, float], tuple[None, None]]:
    """Converts Lambert-93 coordinates (x, y) to GPS coordinates (lon, lat)."""
    try:
        lon, lat = _transformer.transform(x, y)
        logging.debug(f"Successfully converted ({x}, {y}) -> ({lon}, {lat})")
        return lon, lat
    except Exception as e:
        logging.warning(f"Error converting coordinates ({x}, {y}): {e}")
        return None, None


def load_coverage_data(filepath: str) -> pd.DataFrame:
    """Loads network coverage data from a CSV file and converts Lambert93 coordinates to GPS (lat, lon)."""
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return pd.DataFrame()
    try:
        data = pd.read_csv(filepath, delimiter=',')
        logging.debug(f"Successfully loaded CSV: {filepath} with shape {data.shape}")
        if 'lat' not in data.columns or 'lon' not in data.columns:
            logging.info("Converting x, y to lat, lon")
            data[['lon', 'lat']] = data.apply(lambda row: lambert93_to_gps(row['x'], row['y']), axis=1,
                                              result_type='expand')
        logging.debug(f"Converted CSV columns: {data.columns.tolist()}")
        return data
    except Exception as e:
        logging.error(f"Unable to read CSV file: {e}")
        return pd.DataFrame()
