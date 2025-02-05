#!/bin/bash

# Installation des dépendances Python si nécessaire
if [ ! -d "venv" ]; then
    echo "🔧 Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installation des dépendances..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Lancement de l'application Flask
echo "🚀 Démarrage du serveur..."
export FLASK_APP=backend/app.py
export FLASK_ENV=development
flask run
