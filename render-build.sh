#!/usr/bin/env bash
# Script de build pour Render avec PostgreSQL

echo "Demarrage du build sur Render avec PostgreSQL..."

# Installer les dependances
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Creer/Mettre a jour la configuration d'entreprise
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

print('Configuration entreprise KBIS IMMOBILIER creee avec succes!')
print('Base de donnees PostgreSQL configuree!')
print('Build termine avec succes!')
"

echo "Build termine avec PostgreSQL!"
