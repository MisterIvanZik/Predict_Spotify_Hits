import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
import os
import time
import pickle
import concurrent.futures
from dotenv import load_dotenv

# 🔹 Chargement des variables d'environnement
load_dotenv()

# 🔹 Connexion à l'API Spotify
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# 🔹 Cache pour stocker les résultats et éviter les appels répétés
CACHE_FILE = "spotify_cache.pkl"
track_info_cache = {}
artist_info_cache = {}

def save_cache():
    with open(CACHE_FILE, "wb") as f:
        pickle.dump((track_info_cache, artist_info_cache), f)

def load_cache():
    global track_info_cache, artist_info_cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            track_info_cache, artist_info_cache = pickle.load(f)

# 🔹 Extraction automatique du **continent** et du **pays** à partir du chemin du fichier
def extract_continent_and_country(file_path):
    parts = file_path.split(os.sep)
    if len(parts) >= 2:
        continent = parts[-2]
        filename = parts[-1]
        country = filename.split("_")[-1].replace(".csv", "")
        return continent, country
    return None, None

# 🔹 Récupération des morceaux en batchs (50 par requête)
def get_tracks_in_batches(batch_ids):
    while True:
        try:
            return sp.tracks(batch_ids)["tracks"]
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", 5))
                print(f"⚠️ Rate limit atteint. Pause de {retry_after} secondes...")
                time.sleep(retry_after)
            else:
                print(f"⚠️ Erreur API : {e}")
                return []

# 🔹 Récupération des infos des morceaux
def process_track(track, artist_name):
    if not track:
        return None
    try:
        track_id = track["id"]
        artist_id = track["artists"][0]["id"] if track["artists"] else None

        # 🔹 Vérifie si l'info est déjà en cache
        if track_id in track_info_cache:
            return track_info_cache[track_id]

        # 🔹 Récupération des infos de l'artiste
        if artist_id in artist_info_cache:
            artist_info = artist_info_cache[artist_id]
        else:
            artist_info = sp.artist(artist_id) if artist_id else {"genres": [], "images": []}
            artist_info_cache[artist_id] = artist_info

        # 🔹 Nombre d'auditeurs mensuels (followers)
        monthly_listeners = artist_info["followers"]["total"]

        # 🔹 Récupération des images
        track_image = track["album"]["images"][0]["url"] if track["album"]["images"] else None
        artist_image = artist_info["images"][0]["url"] if artist_info["images"] else None

        track_info = {
            "track_id": track_id,
            "popularity": track["popularity"],
            "duration_ms": track["duration_ms"],
            "explicit": track["explicit"],
            "genre": artist_info["genres"][0] if artist_info["genres"] else None,
            "release_date": track["album"]["release_date"],
            "track_image": track_image,
            "artist_image": artist_image,
            "monthly_listeners": monthly_listeners
        }

        # 🔹 Ajoute au cache
        track_info_cache[track_id] = track_info
        return track_info

    except Exception as e:
        print(f"⚠️ Erreur lors du traitement d'un morceau : {e}")
        return None

# 🔹 Récupère les informations pour plusieurs morceaux
def get_tracks_info(track_ids, artist_names):
    track_data = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(0, len(track_ids), 50):
            batch_ids = track_ids[i:i+50]
            futures.append(executor.submit(get_tracks_in_batches, batch_ids))

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="🔍 Récupération des morceaux"):
            tracks = future.result()
            for track, artist_name in zip(tracks, artist_names[i:i+50]):
                track_info = process_track(track, artist_name)
                if track_info:
                    track_data.append(track_info)

    return pd.DataFrame(track_data)

# 🔹 Enrichissement des fichiers CSV
def enrich_multiple_csv_with_spotify_data(input_files, output_base_folder):
    if not os.path.exists(output_base_folder):
        os.makedirs(output_base_folder)

    for input_file in input_files:
        continent, country = extract_continent_and_country(input_file)
        if not continent or not country:
            print(f"❌ Impossible d'extraire les informations du fichier {input_file}")
            continue

        # 🔹 Création des dossiers automatiquement
        output_folder = os.path.join(output_base_folder, continent)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_file = os.path.join(output_folder, f"charts_{country}.csv")
        print(f"📥 Traitement du fichier : {input_file}")

        df = pd.read_csv(input_file)

        if 'track_id' not in df.columns or 'artist_names' not in df.columns:
            print(f"❌ Colonnes manquantes dans {input_file}")
            continue

        track_ids = df["track_id"].unique()
        artist_names = df["artist_names"].tolist()

        print(f"🔍 Récupération des données Spotify pour {len(track_ids)} morceaux...")

        df_spotify = get_tracks_info(track_ids, artist_names)
        if df_spotify.empty:
            print(f"❌ Échec de récupération des données pour {input_file}.")
            continue

        df_merged = df.merge(df_spotify, on="track_id", how="left")
        df_merged.to_csv(output_file, index=False)
        print(f"✅ Fichier enrichi {output_file} créé avec succès !")

        # 🔹 Sauvegarde du cache après chaque fichier
        save_cache()

# 🔹 Exemple d'utilisation
if __name__ == "__main__":
    input_files = [
        "Charts_no_info/Charts_North_America/charts_CAN🇨🇦.csv",
        "Charts_no_info/Charts_North_America/charts_USA🇺🇸.csv",
        "Charts_no_info/Charts_North_America/charts_MEX🇲🇽.csv",

        "Charts_no_info/Charts_Asia/charts_ARE🇦🇪.csv",
        "Charts_no_info/Charts_Asia/charts_IDN🇮🇩.csv",
        "Charts_no_info/Charts_Asia/charts_IND🇮🇳.csv",
        "Charts_no_info/Charts_Asia/charts_JPN🇯🇵.csv",
        "Charts_no_info/Charts_Asia/charts_KOR🇰🇷.csv",
        "Charts_no_info/Charts_Asia/charts_SAU🇸🇦.csv",
        "Charts_no_info/Charts_Asia/charts_THA🇹🇭.csv",
        "Charts_no_info/Charts_Asia/charts_TUR🇹🇷.csv",

        "Charts_no_info/Charts_Europe/charts_BEL🇧🇪.csv",
        "Charts_no_info/Charts_Europe/charts_DNK🇩🇰.csv",
        "Charts_no_info/Charts_Europe/charts_ESP🇪🇸.csv",
        "Charts_no_info/Charts_Europe/charts_FIN🇫🇮.csv",
        "Charts_no_info/Charts_Europe/charts_FRA🇫🇷.csv",
        "Charts_no_info/Charts_Europe/charts_GBR🇬🇧.csv",
        "Charts_no_info/Charts_Europe/charts_ITA🇮🇹.csv",
        "Charts_no_info/Charts_Europe/charts_NOR🇳🇴.csv",

        "Charts_no_info/Charts_Oceania/charts_AUS🇦🇺.csv",
        "Charts_no_info/Charts_Oceania/charts_NZL🇳🇿.csv",

        "Charts_no_info/Charts_South_America/charts_ARG🇦🇷.csv",
        "Charts_no_info/Charts_South_America/charts_BOL🇧🇴.csv",
        "Charts_no_info/Charts_South_America/charts_BRA🇧🇷.csv",
        "Charts_no_info/Charts_South_America/charts_CHL🇨🇱.csv",
        "Charts_no_info/Charts_South_America/charts_COL🇨🇴.csv",
        "Charts_no_info/Charts_South_America/charts_VEN🇻🇪.csv",

        "Charts_no_info/Charts_Africa/charts_EGY🇪🇬.csv",
        "Charts_no_info/Charts_Africa/charts_MAR🇲🇦.csv",
        "Charts_no_info/Charts_Africa/charts_NGA🇳🇬.csv",
        "Charts_no_info/Charts_Africa/charts_ZAF🇿🇦.csv",
    ]
    output_folder = "Charts_with_info"
    load_cache()
    enrich_multiple_csv_with_spotify_data(input_files, output_folder)
