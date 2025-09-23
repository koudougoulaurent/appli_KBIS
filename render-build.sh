#!/usr/bin/env bash
# Script de build pour Render

echo "Demarrage du build sur Render..."

# Installer les dependances
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Creer la configuration d'entreprise
python manage.py shell -c "
from core.models import ConfigurationEntreprise

# Creer la configuration d'entreprise si elle n'existe pas
config, created = ConfigurationEntreprise.objects.get_or_create(
    nom_entreprise='KBIS IMMOBILIER',
    defaults={
        'adresse': '123 Rue de l\\'Immobilier',
        'ville': 'Ouagadougou',
        'code_postal': '01 BP 1234',
        'telephone': '+226 25 12 34 56',
        'email': 'contact@kbis.bf',
        'actif': True
    }
)

if created:
    print('Configuration entreprise creee')
else:
    print('Configuration entreprise existante mise a jour')
    config.nom_entreprise = 'KBIS IMMOBILIER'
    config.save()

print('Build termine avec succes!')
"

echo "Build termine!"
