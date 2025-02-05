from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
import json
from collections import defaultdict

app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')
CORS(app)

# Dossiers des données
CHARTS_DIR = "../Charts_with_info"

def load_all_data():
    """Charge toutes les données des charts en mémoire"""
    all_data = {}
    for continent in os.listdir(CHARTS_DIR):
        continent_path = os.path.join(CHARTS_DIR, continent)
        if os.path.isdir(continent_path):
            all_data[continent] = {}
            for file in os.listdir(continent_path):
                if file.endswith('.csv'):
                    country_code = file.split('_')[1].split('.')[0]
                    file_path = os.path.join(continent_path, file)
                    all_data[continent][country_code] = pd.read_csv(file_path)
    return all_data

# Charger les données au démarrage
CHARTS_DATA = load_all_data()

@app.route('/api/search')
def search_track():
    """Recherche une chanson par nom et/ou artiste"""
    query = request.args.get('query', '').lower()
    
    if not query:
        return jsonify([])
    
    results = []
    for continent_data in CHARTS_DATA.values():
        for country_data in continent_data.values():
            tracks = country_data.to_dict('records')
            for track in tracks:
                if (query in track['track_name'].lower() or 
                    query in track['artist_names'].lower()):
                    # Éviter les doublons en vérifiant si le track_id existe déjà
                    if not any(r['track_id'] == track['track_id'] for r in results):
                        results.append({
                            'track_id': track['track_id'],
                            'track_name': track['track_name'],
                            'artist_names': track['artist_names'],
                            'track_image': track['track_image'],
                            'popularity': track['popularity'],
                            'streams': track['streams'],
                            'country': track['country']
                        })
    
    # Trier par popularité et limiter à 10 résultats
    results.sort(key=lambda x: x['popularity'], reverse=True)
    return jsonify(results[:10])

@app.route('/')
def index():
    """Route principale qui affiche le dashboard"""
    return render_template('index.html')

@app.route('/api/continents')
def get_continents():
    """Retourne la liste des continents disponibles"""
    continents = [continent.replace('Charts_', '') for continent in os.listdir(CHARTS_DIR)
                 if os.path.isdir(os.path.join(CHARTS_DIR, continent))]
    return jsonify(continents)

@app.route('/api/countries/<continent>')
def get_countries(continent):
    """Retourne la liste des pays pour un continent donné"""
    continent_dir = f"Charts_{continent}"
    continent_path = os.path.join(CHARTS_DIR, continent_dir)
    
    if not os.path.exists(continent_path):
        return jsonify({'error': 'Continent non trouvé'}), 404
    
    countries = []
    for file in os.listdir(continent_path):
        if file.endswith('.csv'):
            country_code = file.split('_')[1].split('.')[0]
            # Extraire l'emoji du pays (2 derniers caractères)
            flag = country_code[-2:] if len(country_code) > 2 else ''
            name = country_code[:-2] if len(country_code) > 2 else country_code
            countries.append({
                'code': name,
                'name': name,
                'flag': flag
            })
    
    return jsonify(countries)

@app.route('/api/charts/<continent>/<country>')
def get_charts_data(continent, country):
    """Retourne les données des charts pour un pays donné"""
    continent_key = f"Charts_{continent}"
    
    if continent_key not in CHARTS_DATA:
        return jsonify({'error': 'Continent non trouvé'}), 404
    
    country_data = None
    for country_code, data in CHARTS_DATA[continent_key].items():
        if country in country_code:
            country_data = data
            break
    
    if country_data is None:
        return jsonify({'error': 'Pays non trouvé'}), 404

    # Préparer les données pour le frontend
    latest_data = country_data.sort_values('week_date').groupby('track_id').last().reset_index()
    top_tracks = latest_data.nlargest(10, 'streams')[
        ['track_name', 'artist_names', 'streams', 'popularity', 'track_image']
    ].to_dict('records')

    # Calculer l'évolution de la popularité
    popularity_trends = country_data.groupby('week_date')['popularity'].mean().reset_index()
    popularity_trends['week_date'] = pd.to_datetime(popularity_trends['week_date']).dt.strftime('%Y-%m-%d')
    
    return jsonify({
        'top_tracks': top_tracks,
        'popularity_trends': popularity_trends.to_dict('records')
    })

if __name__ == '__main__':
    app.run(debug=True)
