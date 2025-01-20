from typing import Dict, Tuple

import httpx
import pandas as pd
import uvicorn

from fastapi import FastAPI, HTTPException
from geopy.distance import geodesic
from pydantic import BaseModel
from app.utils import load_coverage_data

app = FastAPI()

network_coverage_data = load_coverage_data('data/Sites_mobiles_2G_3G_4G_France.csv')


class AddressRequest(BaseModel):

    addresses: Dict[str, str]


client = httpx.AsyncClient()


async def fetch_address_to_coordinates(address: str) -> Tuple[float, float]:
    response = await client.get(f'https://api-adresse.data.gouv.fr/search/?q={address}')
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Can't get coordinates for address {address}")
    data = response.json()
    if not data['features']:
        raise HTTPException(status_code=404, detail=f"No coordinates found for address {address}")
    coordinates = data['features'][0]['geometry']['coordinates']
    return coordinates[0], coordinates[1]


def check_coverage(lon: float, lat: float, dataframe: pd.DataFrame) -> Dict[str, Dict[str, bool]]:
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


async def get_coverage_datas(request: AddressRequest) -> Dict[str, Dict[str, bool]]:
    results = {}
    for address_id, address in request.addresses.items():
        lon, lat = await fetch_address_to_coordinates(address)
        results[address_id] = check_coverage(lon, lat, network_coverage_data)
    return results


@app.get("/")
async def start_endpoint() -> Dict[str, str]:
    return {"message": "Welcome to the Network Coverage API"}


@app.post("/coverage")
async def get_coverage_endpoint_response(request: AddressRequest) -> Dict[str, Dict[str, bool]]:
    return await get_coverage_datas(request)


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
