#!/bin/bash
echo "🚀 Démarrage du build sur Render..."

# Installation des dépendances
pip install -r requirements.txt

# Application des migrations
python manage.py migrate

# Initialisation des données de test
python init_render_users.py

echo "✅ Build terminé avec succès!"