#!/bin/bash
# Script de démarrage pour Render
# S'exécute automatiquement au déploiement

echo "🚀 DÉMARRAGE DE L'APPLICATION SUR RENDER"
echo "========================================"

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
sleep 5

# Exécuter les migrations
echo "📦 Exécution des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Initialiser les données de base
echo "🔧 Initialisation des données de base..."
python manage.py init_render

# Démarrer l'application
echo "🌐 Démarrage de l'application..."
exec gunicorn gestion_immobiliere.wsgi:application --bind 0.0.0.0:$PORT
