import pandas as pd
from collections import defaultdict
import os

# 🔹 Liste des genres ou mots-clés associés à des saisons
season_keywords = {
    "christmas": "Christmas",
    "holiday": "Holiday",
    "winter": "Winter",
    "summer": "Summer",
    "halloween": "Halloween"
}

# 🔹 Mapping des codes de pays vers les emojis de drapeaux
country_to_flag = {
    "can": "🇨🇦", "usa": "🇺🇸", "mex": "🇲🇽",
    "are": "🇦🇪", "idn": "🇮🇩", "ind": "🇮🇳", "jpn": "🇯🇵", "kor": "🇰🇷", "sau": "🇸🇦", "tha": "🇹🇭", "tur": "🇹🇷",
    "bel": "🇧🇪", "dnk": "🇩🇰", "esp": "🇪🇸", "fin": "🇫🇮", "fra": "🇫🇷", "gbr": "🇬🇧", "ita": "🇮🇹", "nor": "🇳🇴",
    "aus": "🇦🇺", "nzl": "🇳🇿",
    "arg": "🇦🇷", "bol": "🇧🇴", "bra": "🇧🇷", "chl": "🇨🇱", "col": "🇨🇴", "ven": "🇻🇪",
    "egy": "🇪🇬", "mar": "🇲🇦", "nga": "🇳🇬", "zaf": "🇿🇦"
}

# 🔹 Charger un fichier et identifier le pays et le continent
def load_country_data(file_path):
    # Extraire le nom du fichier et le pays
    file_name = os.path.basename(file_path)
    country_code = file_name.split("_")[-1].replace(".csv", "").lower()

    # Extraire le continent à partir du chemin du fichier
    continent = file_path.split("/")[-2].replace("Charts_", "").replace("_", " ")

    df = pd.read_csv(file_path)
    df["country"] = country_code
    df["continent"] = continent
    return df

# 🔹 Rechercher une chanson dans un fichier
def search_tracks(df, track_name, artist_name):
    if 'track_name' not in df.columns or 'artist_names' not in df.columns:
        print("⚠️ Les colonnes 'track_name' et 'artist_names' sont requises dans le fichier CSV.")
        return None

    results = df[
        (df['track_name'].str.contains(track_name, case=False, na=False)) &
        (df['artist_names'].str.contains(artist_name, case=False, na=False))
    ]
    return results.drop_duplicates(subset=["track_name", "artist_names"]) if not results.empty else None

# 🔹 Analyser la popularité de la chanson par pays
def analyze_popularity(files, song_name, artist_name):
    country_popularity = []
    continent_count = defaultdict(int)
    total_countries_per_continent = defaultdict(int)
    country_streams = {}
    song_details = {}
    seasonal_message = ""

    for file in files:
        df = load_country_data(file)
        country = df["country"].iloc[0]
        continent = df["continent"].iloc[0]
        total_countries_per_continent[continent] += 1

        tracks = search_tracks(df, song_name, artist_name)
        if tracks is not None:
            for _, track in tracks.iterrows():
                if track["rank"] <= 10 and track["weeks_on_chart"] > 2:
                    country_popularity.append(country)
                    continent_count[continent] += 1
                    country_streams[country] = track["streams"]

                    if not song_details:
                        song_details = {
                            "release_date": track.get("release_date", "N/A"),
                            "genre": track.get("genre", "Unknown"),
                            "track_image": track.get("track_image", ""),
                            "artist_image": track.get("artist_image", "")
                        }

                    # 🔹 Détection automatique de la saison
                    genre = track.get("genre", "").lower()
                    for keyword, season in season_keywords.items():
                        if keyword in genre:
                            seasonal_message = f"\n🎄 Tracks for {season}!"
                            break

    # 🔹 Déterminer la popularité par continent
    popular_continents = [
        continent for continent, count in continent_count.items()
        if count > total_countries_per_continent[continent] / 2  # Populaire dans plus de la moitié des pays du continent
    ]

    # 🔹 Chanson internationale ?
    is_international = len(popular_continents) >= 3  # Populaire dans plus de 3 continents

    return country_popularity, popular_continents, is_international, country_streams, song_details, seasonal_message

# 🔹 Fichiers des classements
files = [
    "Charts_with_info/Charts_North_America/charts_CAN🇨🇦.csv",
    "Charts_with_info/Charts_North_America/charts_USA🇺🇸.csv",
    "Charts_with_info/Charts_North_America/charts_MEX🇲🇽.csv",
    "Charts_with_info/Charts_Asia/charts_ARE🇦🇪.csv",
    "Charts_with_info/Charts_Asia/charts_IDN🇮🇩.csv",
    "Charts_with_info/Charts_Asia/charts_IND🇮🇳.csv",
    "Charts_with_info/Charts_Asia/charts_JPN🇯🇵.csv",
    "Charts_with_info/Charts_Asia/charts_KOR🇰🇷.csv",
    "Charts_with_info/Charts_Asia/charts_SAU🇸🇦.csv",
    "Charts_with_info/Charts_Asia/charts_THA🇹🇭.csv",
    "Charts_with_info/Charts_Asia/charts_TUR🇹🇷.csv",
    "Charts_with_info/Charts_Europe/charts_BEL🇧🇪.csv",
    "Charts_with_info/Charts_Europe/charts_DNK🇩🇰.csv",
    "Charts_with_info/Charts_Europe/charts_ESP🇪🇸.csv",
    "Charts_with_info/Charts_Europe/charts_FIN🇫🇮.csv",
    "Charts_with_info/Charts_Europe/charts_FRA🇫🇷.csv",
    "Charts_with_info/Charts_Europe/charts_GBR🇬🇧.csv",
    "Charts_with_info/Charts_Europe/charts_ITA🇮🇹.csv",
    "Charts_with_info/Charts_Europe/charts_NOR🇳🇴.csv",
    "Charts_with_info/Charts_Oceania/charts_AUS🇦🇺.csv",
    "Charts_with_info/Charts_Oceania/charts_NZL🇳🇿.csv",
    "Charts_with_info/Charts_South_America/charts_ARG🇦🇷.csv",
    "Charts_with_info/Charts_South_America/charts_BOL🇧🇴.csv",
    "Charts_with_info/Charts_South_America/charts_BRA🇧🇷.csv",
    "Charts_with_info/Charts_South_America/charts_CHL🇨🇱.csv",
    "Charts_with_info/Charts_South_America/charts_COL🇨🇴.csv",
    "Charts_with_info/Charts_South_America/charts_VEN🇻🇪.csv",
    "Charts_with_info/Charts_Africa/charts_EGY🇪🇬.csv",
    "Charts_with_info/Charts_Africa/charts_MAR🇲🇦.csv",
    "Charts_with_info/Charts_Africa/charts_NGA🇳🇬.csv",
    "Charts_with_info/Charts_Africa/charts_ZAF🇿🇦.csv",
]

# 🔹 Entrée utilisateur avec emojis
track_name = input("🎶 Entrez le titre de la chanson : ").strip()
artist_name = input("🎤 Entrez le nom de l'artiste : ").strip()

# 🔹 Analyse des résultats
countries, continents, international, streams, details, seasonal_message = analyze_popularity(files, track_name, artist_name)

# 🔹 Détails de la chanson
print("\n**Détails de la chanson :**")
print(f"   - Date de sortie : {details.get('release_date', 'N/A')}")
print(f"   - Genre : {details.get('genre', 'Unknown')}")
print(f"   - Image du titre : {details.get('track_image', 'Non disponible')}")
print(f"   - Image de l'artiste : {details.get('artist_image', 'Non disponible')}")

# 🔹 Affichage des résultats avec emojis
print("\n🔍 **Analyse de la popularité**")
if countries:
    # Ajouter les drapeaux aux noms des pays
    countries_with_flags = [f"{country}{country_to_flag.get(country, '')}" for country in countries]
    print(f"✅ Cette chanson est populaire dans les pays suivants : {', '.join(countries_with_flags)}")
    for country, stream_count in streams.items():
        print(f"   - {country}{country_to_flag.get(country, '')}: {stream_count} streams")

if continents:
    print(f"🌍 Elle est populaire dans ces continents : {', '.join(continents)}")
    if international:
        print("🏆 **Cette chanson est un hit international !**")

print(seasonal_message)
