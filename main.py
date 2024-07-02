from contextlib import asynccontextmanager
from typing import Dict

import httpx

from fastapi import FastAPI, HTTPException
from geopy.distance import geodesic
from pydantic import BaseModel

from app import utils
from app.utils import load_coverage_data


# =>définition d'un modèle de données en utilisant Pydantic
# ce modèle sera utilisé pr valid données et sérializ° données recues / l'API
# BaseModel = 1 classe de Pydantic
class AddressRequest(BaseModel):
    # class AdressRequest qui hérite de BaseModel de Pydantic

    addresses: Dict[str, str]
    # class a un attribut 'adresses' de type ...

app = FastAPI()
coverage_data = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global coverage_data
    coverage_data = utils.load_coverage_data('./test.csv')
    yield

app.lifespan = lifespan

@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.post("/coverage")
# Route accepte des requêtes contenant des données JSON qui dvent = valid / modèle 'AddressRequest'
async def get_coverage(request: AddressRequest):
    results = {}
    #coverage_data = "Sites_mobiles_2G_3G_4G_France.csv"
    #df = utils.load_coverage_data(coverage_data)
    async with httpx.AsyncClient() as client:
        # // pourquoi ds un context manager ?
        # Utilisation de httpx.AsyncClient pr permettre requêtes asynchrones
        for adress_id, address in request.addresses.items():
            # Itération sur ch adresse fournie ds la requête
            response = await client.get(f'https://api-adresse.data.gouv.fr/search/?q={address}')
            # Pas un post ?
            # envoie requête GET à l'API d'adresse gouv pr obtenir coord GPS de l'adresse spécifiée
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Error fetching coordinates for address {address}")

            data = response.json()
            if not data['features']:
                raise HTTPException(status_code=404, detail=f"No coordinates found for address {address}")

            coordinates = data['features'][0]['geometry']['coordinates']
            lon, lat = coordinates[0], coordinates[1]

            # Vérifier la couverture pour chaque opérateur en fction des coord GPS gotten
            #print('longitude:', lon, lat, df)
            print(coverage_data)
            results[adress_id] = check_coverage(lon, lat, coverage_data)
            print(results)
    return results


def check_coverage(lon, lat, data):
    coverage_result = {}
    # stockera les résult de cverture pr ch opérateur
    for _, row in data.iterrows():
        # iterrows = méthode de pandas qui permet d'itérer sur les lignes d'un Dataframe
        # _ car on n'a pas besoin de l'index de la ligne
        operator = row['Operateur']
        # On extrait le nom de l'opérateur de la ligne
        if operator not in coverage_result:
            # 'If Orange not in result'
            coverage_result[operator] = {"2G": False, "3G": False, "4G": False}
            # {'Orange': {}}
        if row['2G'] == 1 and not coverage_result[operator]["2G"] and geodesic((lat, lon), (row['lat'], row['lon'])).km <= 30:
            # calcul distance entre l'adresse spécifiée (lat, lon) et la tour r (row['y'], row['x']),
            # en km, et vérif si cette distance <= 30km
            coverage_result[operator]["2G"] = True
            # m à jr la couverture 2G pr cet opérateur à True
        if row['3G'] == 1 and not coverage_result[operator]["3G"] and geodesic((lat, lon), (row['lat'], row['lon'])).km <= 5:
            coverage_result[operator]["3G"] = True
        if row['4G'] == 1 and not coverage_result[operator]["4G"] and geodesic((lat, lon), (row['lat'], row['lon'])).km <= 10:
            coverage_result[operator]["4G"] = True
    return coverage_result

