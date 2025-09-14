#!/bin/bash
# Script de démarrage pour Render
# S'exécute automatiquement au déploiement

echo "🚀 DÉMARRAGE DE L'APPLICATION SUR RENDER"
echo "========================================"

# Forcer la variable d'environnement Django
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings
echo "✅ Configuration Django: $DJANGO_SETTINGS_MODULE"

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
sleep 5

# Exécuter les migrations
echo "📦 Exécution des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Sauvegarder les données existantes (si elles existent)
echo "💾 Sauvegarde des données existantes..."
python sauvegarder_donnees.py || echo "ℹ️  Aucune donnée existante à sauvegarder"

# Vérifier et créer les données automatiquement
echo "🔧 Vérification automatique des données..."
python verifier_donnees_automatique.py

# Démarrer l'application
echo "🌐 Démarrage de l'application..."
exec gunicorn gestion_immobiliere.wsgi:application --bind 0.0.0.0:$PORT
