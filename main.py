

import logging
import os

import httpx
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from geopy.distance import geodesic
from pydantic import BaseModel

from app.utils import load_coverage_data

logging.basicConfig(level=logging.INFO)

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

csv_path = "data/Sites_mobiles_TEST.csv"

if not os.path.exists(csv_path):
    raise FileNotFoundError("CSV file NOT found!")

try:
    network_coverage_data = load_coverage_data(csv_path)
    logging.info(f"CSV loaded successfully! Shape: {network_coverage_data.shape}")
except Exception as e:
    logging.error(f"Error reading CSV: {e}")

app = FastAPI()


class AddressRequest(BaseModel):

    addresses: dict[str, str]


client = httpx.AsyncClient()


async def fetch_address_to_coordinates(address: str):
    """Fetch GPS coordinates for a given address."""
    logging.info(f"Fetching coordinates for address: {address}")
    try:
        response = await client.get(f'https://api-adresse.data.gouv.fr/search/?q={address}')
        response.raise_for_status()
        data = response.json()
        if not data['features']:
            return None
        coordinates = data['features'][0]['geometry']['coordinates']
        return coordinates[0], coordinates[1]
    except Exception as err:
        logging.error(f"Unexpected error fetching {address}: {err}")
        return None


def check_coverage(lon: float, lat: float, dataframe: pd.DataFrame) -> dict[str, dict[str, bool]]:
    """Check if an address is covered by 2G, 3G, 4G networks"""
    coverage_result = {}
    for index, row in dataframe.iterrows():
        operator = row['Operateur']
        if operator not in coverage_result:
            coverage_result[operator] = {"2G": False, "3G": False, "4G": False}
        if row['2G'] == 1 and not coverage_result[operator]["2G"] and geodesic((lat, lon),
                                                                               (row['lat'], row['lon'])).km <= 30:
            coverage_result[operator]["2G"] = True
        if row['3G'] == 1 and not coverage_result[operator]["3G"] and geodesic((lat, lon),
                                                                               (row['lat'], row['lon'])).km <= 5:
            coverage_result[operator]["3G"] = True
        if row['4G'] == 1 and not coverage_result[operator]["4G"] and geodesic((lat, lon),
                                                                               (row['lat'], row['lon'])).km <= 10:
            coverage_result[operator]["4G"] = True
    return coverage_result


async def get_coverage_datas(request: AddressRequest) -> dict[str, dict[str, str] | dict[str, dict[str, bool]]]:
    """Process coverage requests"""
    results = {}
    for address_id, address in request.addresses.items():
        lon, lat = await fetch_address_to_coordinates(address)
        if lon is None or lat is None:
            results[address_id] = {"error": "Could not retrieve coordinates"}
            continue
        results[address_id] = check_coverage(lon, lat, network_coverage_data)
    return results


@app.get("/")
async def root():
    return {"message": "Welcome to Network Coverage API!"}


@app.post("/coverage")
async def get_coverage_endpoint_response(request: AddressRequest):
    try:
        return await get_coverage_datas(request)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

