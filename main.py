from typing import Dict

import httpx

from fastapi import FastAPI, HTTPException
from geopy.distance import geodesic
# bibl -> calculer dist entre deux pts géog en km
from pydantic import BaseModel
# BaseModel -> def modèle données avec des type sstricts
# A la réception requête, FastAPI utilise ce modèle pr valid auto données requête entrante

from app import utils

app = FastAPI()
# FastAPI() = 1 classe fourni / framework FastAPI -> En appelant FastAPI() -> création d'une instance de cette classe, ce qui
# réprésente mon application
# L'instance app est utilisée pr déf routes de votre application
# ajout routes > décorarateur '@app.get()' etc..
# Ces déco lient fctions Python spécifiques à des chemins URl et des méthodes HTTP
# ->Simplicité & clarté = 1 instance unique 'app' pr gérer ttes routes app
# perf = FastAPI = basé / ASGI et offre une gestion asynchr requêtes -> amélior° perf application

# Cette instance dt = global pr = accessible par ttes les routes déf ds l'application
# Cette place au niveau global -> ttes routes & config ajoutées ensuite se réfèrent à cette instance


network_coverage_data = utils.load_coverage_data('./Sites_mobiles_2G_3G_4G_France.csv')
# = appelé une seule fois lors du démrrage application
# import module utils qui contient la fction
# cette fction lit le fichier CSV et retourn données
# une fois données chargées par la fction, stock ds variable network_coverage_data


# classe doit = défini avt son utilisation ds routes ou fonctions
class AdressRequest(BaseModel):
    # class AdressRequest qui hérite de BaseModel dans FastAPI
    # données JSON requête = converties en une instance d'AdressRequest
    # Si données requête ≠ correspdt modèle -> FastAPI -> erreur

    addresses: Dict[str, str]
    # classe AdressRequest a un attribut 'adresses' de type ... -> chaque instance de la classe AdressRequest aura cet attribut


client = httpx.AsyncClient()
# classe qui -> effect requêtes HTTP de man asynch
# en l'instanciant ainsi, ns créeons un client CTTP prêt à être utilisé pr envoy requêtes


async def fetch_adress_to_coordinates(address: str) -> tuple:
    response = await client.get(f'https://api-adresse.data.gouv.fr/search/?q={address}')
    # envoi une requête GET à l'url spécifiée avec l'adresse fournie ds la requête
    # keyword 'await' indique à Python d'attendre la réponse de cette requête avt de continuer l'exéc du code
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Can't get coordinates for address {address}")
    data = response.json()
    # cversion contenu réponse
    if not data['features']:
        raise HTTPException(status_code=404, detail=f"No coordinates found for address {address}")
    # fin vérifs avec succès
    coordinates = data['features'][0]['geometry']['coordinates']
    return coordinates[0], coordinates[1]


def check_coverage(lon, lat, dataframe):
# rajouter typing: prd .... -> dict
# prd en param longit, latit et un df pandans et retourne un dict qui contient infos sur
# couverture réseau pr ≠ opérateurs en fonction des coord GPS fournies
    coverage_result = {}
    for index, row in dataframe.iterrows():
    # itération sur ch ligne du dataframe
    # ch ligne = une tour de télcommunication ac infos sur opérateur et couverture réseau
        operator = row['Operateur']
        # extraction du nom de l'opérateur à partir de la colonne 'opérateur'
        # voir des exemples
        if operator not in coverage_result:
            coverage_result[operator] = {"2G": False, "3G": False, "4G": False}
            # si l'opérateur n'est pas présent, itialis° d'un nvel élément ds le dict avec clés 2G... initialisées à False
            # permet de s'assurer qu'on a une struct de dict pr ch opérateur
        if row['2G'] == 1 and not coverage_result[operator]["2G"] and geodesic((lat, lon), (row['lat'], row['lon'])).km <= 30:
        # ? couvert réseau = dispo pr cette technologie à cette tour
        # ? couvert réseau pr cette tech n'a pas déjà été marquée à True
        # ? dist entre coord adresse fournie et coord tour de télécommunication <= à une cert dist critiq
            coverage_result[operator]["2G"] = True
            # cette tech de réseau est dispo pr cet opérateur à proxim de l'adresse spécifiée
        if row['3G'] == 1 and not coverage_result[operator]["3G"] and geodesic((lat, lon), (row['lat'], row['lon'])).km <= 5:
            coverage_result[operator]["3G"] = True
        if row['4G'] == 1 and not coverage_result[operator]["4G"] and geodesic((lat, lon), (row['lat'], row['lon'])).km <= 10:
            coverage_result[operator]["4G"] = True
    return coverage_result
    # infos sur cverture réseau de ch opérateur ap av parcouru ttes lignes du dataframe


async def get_coverage_datas(request: AdressRequest):
    results = {}
    # va stocker les résultats de la cverture pr ch adresse fournie ds la requête
    for address_id, address in request.addresses.items():
    # FastAPi utilise Pydantic pr vérif que le corps requête contient une clé 'Adresses' avec comme valeurs un dict de str
    # FastAPI crée alors une instance d'AdressRequest avec adresses défini à
    # Ds une vue par ex, je peux utiliser request.adresses ss avoir à parser et valid manuellement les données JSON
    # + = Sécu et robustesse = données sont validées avt d'atteindre logique métier => réduct° risques d'erreurs
    # + = docu auto = doc API = généré auto / FastAPI à partir de ces modèles -> Facilite compr & utilis° API / autres dév
    # Itération sur ch adresse fournie ds la requête
    # itère sur la paire '(adress_id, adress)' du dictionnaire 'adresses' de l'objet request
        lon, lat = await fetch_adress_to_coordinates(address)
        # appel de la fonction 'fetch_adress_to_coordinates' pr obtenir coord de l'adresse spécifiée
        results[address_id] = check_coverage(lon, lat, network_coverage_data)
        # Utilis° des coord obtenues pr vérif la cverture pr ch opérateur de le fichier de données 'network_coverage_data'
        # résult ensuite stockées ds le dict 'results' sous la clé 'address_id'
    return results


@app.get("/")
async def start_endpoint():
    return {"message": "Welcome to the Network Coverage API"}


@app.post("/coverage")
# La fonction ci-dessous gère les requêtes POST sur l'endpoint '/coverage'
# Elle sera appelée qd mon serveur recevra une requête POST à cette url
# Route qui accepte une instance d'AdressRequest, FastAPI st comment extraire et valid données requête
async def get_coverage_endpoint_response(request: AdressRequest):
# param qui représente les données reçues ds le corps de la requête POST
    return await get_coverage_datas(request)
    # await est utilisé pr attendre que 'get_coverage_datas(request)" se termine et renvoie son résultat

# Async/Await nécess ds FastAPI lorsqu'on T avec des fonctions asynch

# En Python, 1 fction définie avec async def = 1 fction asynch
# = Elle pt contenir des operations asynchr qui pvent = suspend temporairement ss bloquer le thread principal
# = crucial pr applications web modernes qui doivent gérer simult de nb requêtes ss bloquer

# Await = à l'int de fctions asynch pr indiq au pgm qu'il dt pause = attendre la fin d'une opération asynch avt de continuer
# Ss lui dire pause, le pgm continueait de courir sans savoir quand les résult de ce qu'ils attendait sont prêts = quand les résult de l'opération asynch seront dispo

# opération asynch = 1 tâche ou une fction qui pt s'exécut de manière indép par rapp au reste du pgm
# ≠ opérations synch, où pgm attend que ch instruction st terminée avt de passer à la suivante, les opérations asynch perm à d'autres parties du pgm de s'exécut pendant qu'elles sont en cours
# Await permet de récupér les résult d'une opération asynchr. Permet de gérer la réponse de l'opération asynch une fois qu'elle est complète

