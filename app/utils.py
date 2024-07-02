import pyproj
# bibl de projection graphique
import pandas as pd


# cvers coord L93 en coord GPS
def lambert93_to_gps(x, y):
    transformer = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
    # 'pyproj.Transformer.from_crs' crée un transformteur de systm de coordonnées qui cvertit les coord d'un systm à un autre
    # "EPSG:2154" = code pr systm de coord Lambert93
    # "EPSG:4326" = code pr systm de coord GPS
    #  'always_xy=True' indique que coord sont tj fournies ds l'ordre (long, lat)
    lon, lat = transformer.transform(x, y)
    # utilise transformateur crée -> cvertir coord 'x' et 'y' de L93 en lon et lat
    return lon, lat
    # retourne tuple


def load_coverage_data(filepath):
    data = pd.read_csv(filepath, delimiter=',')
    # lecture données à partir du fichier CSV spécifié par 'filepath'
    # fction 'pd.read_csv' crée un DataFrame* à partir du fichier CSV -> manipul et analys facilement données tabul
    data[['lon', 'lat']] = data.apply(lambda row: lambert93_to_gps(row['x'], row['y']), axis=1, result_type='expand')
    # transform des données du DF
    # Pdas vérif si les colonnes 'lon' et 'lat' existent déjà, les crée si non, ps affect valeurs
    # methode apply pr appliq une fction lambda à ch ligne('axis=1' = fction = appliq sur ch ligne)
    # Pdas s'attend à ce que la fction lbda retourne qch qui pt = étendu sur plsrs colonnes ac 'result_type='expand'
    # [[]] en pdas pr sélect plsrs colonnes à la fois
    # apply + result_type='expand' -> pdas va retourner un DF si fction appliquée retourne plusieurs valeurs
    return data
    # DF data contient maintenant données initiales du CSV + nvelles colonnes avec coord GPs
