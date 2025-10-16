#!/bin/bash
# Script de configuration PostgreSQL pour Render

echo "🚀 Configuration PostgreSQL pour KBIS Immobilier"
echo "================================================"

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install psycopg2-binary

# Test de connexion
echo "🔍 Test de connexion à PostgreSQL..."
python manage.py dbshell --database=default

# Migration des données
echo "📊 Migration des données..."
python manage.py migrate

# Création du superutilisateur
echo "👤 Création du superutilisateur..."
python manage.py createsuperuser

echo "✅ Configuration terminée!"
