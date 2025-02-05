#!/bin/bash

# Installation des dépendances Python si nécessaire
echo "📦 Installation des dépendances..."
    pip install -r requirements.txt

# Lancement de l'application Flask
echo "🚀 Démarrage du serveur..."
export FLASK_APP=backend/app.py
export FLASK_ENV=development
flask run
