#!/bin/bash
# Script de build pour Render

echo "🚀 Début du build..."

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements_render.txt

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Migration de la base de données
echo "🗄️ Migration de la base de données..."
python manage.py migrate

# Initialisation des données
echo "👥 Initialisation des données..."
python commande_rapide_render.py

echo "✅ Build terminé avec succès !"
