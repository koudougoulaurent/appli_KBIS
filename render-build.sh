#!/usr/bin/env bash
# Script de build pour Render avec PostgreSQL

echo "🚀 Demarrage du build sur Render avec PostgreSQL..."

# Installer les dependances
echo "📦 Installation des dependances..."
pip install -r requirements.txt

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

# Creer/Mettre a jour la configuration d'entreprise
echo "🏢 Configuration de l'entreprise..."
python manage.py shell -c "
from core.models import ConfigurationEntreprise

# Supprimer toutes les configurations existantes
ConfigurationEntreprise.objects.all().delete()

# Creer la nouvelle configuration
config = ConfigurationEntreprise.objects.create(
    nom_entreprise='KBIS IMMOBILIER',
    adresse='123 Rue de l\\'Immobilier',
    ville='Ouagadougou',
    code_postal='01 BP 1234',
    telephone='+226 25 12 34 56',
    email='contact@kbis.bf',
    actif=True
)

print('✅ Configuration entreprise KBIS IMMOBILIER creee avec succes!')
print('✅ Base de donnees PostgreSQL configuree!')
print('✅ Build termine avec succes!')
"

echo "🎉 Build termine avec PostgreSQL!"
