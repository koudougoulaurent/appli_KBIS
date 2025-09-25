#!/usr/bin/env bash
# Script de build pour Render avec PostgreSQL

echo "🚀 Demarrage du build sur Render avec PostgreSQL..."

# Installer les dependances avec Poetry
echo "📦 Installation des dependances avec Poetry..."
poetry install --no-dev

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source $(poetry env info --path)/bin/activate

# Collecter les fichiers statiques
echo "📁 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Tester la connexion PostgreSQL
echo "🔍 Test de la connexion PostgreSQL..."
python -c "
import os
import django
from django.conf import settings
from django.db import connections

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

try:
    db_conn = connections['default']
    with db_conn.cursor() as cursor:
        cursor.execute('SELECT 1')
        print('✅ Connexion PostgreSQL reussie!')
except Exception as e:
    print(f'❌ Erreur de connexion PostgreSQL: {e}')
    exit(1)
"

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate

# Creer/Mettre a jour la configuration d'entreprise et utilisateurs de test
echo "🏢 Configuration de l'entreprise et utilisateurs de test..."
python migrate_users_to_production.py

echo "🎉 Build termine avec PostgreSQL!"
echo "📋 Commandes disponibles:"
echo "   - python manage.py runserver"
echo "   - poetry run gunicorn gestion_immobiliere.wsgi:application"
