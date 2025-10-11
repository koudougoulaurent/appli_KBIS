#!/bin/bash

# Script de création de superuser Django
# Crée un superuser pour l'application KBIS

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}👤 CRÉATION D'UN SUPERUSER DJANGO${NC}"
echo "===================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"

echo -e "\n${YELLOW}1. NAVIGATION VERS L'APPLICATION${NC}"

cd $APP_DIR

# Activer l'environnement virtuel
source venv/bin/activate

echo -e "\n${YELLOW}2. VÉRIFICATION DE LA BASE DE DONNÉES${NC}"

# Vérifier que la base de données est accessible
python3 manage.py check --database default

echo -e "\n${YELLOW}3. MIGRATIONS${NC}"

# Appliquer les migrations si nécessaire
echo "Application des migrations..."
python3 manage.py migrate

echo -e "\n${YELLOW}4. CRÉATION DU SUPERUSER${NC}"

# Créer le superuser
echo "Création du superuser..."
python3 manage.py createsuperuser

echo -e "\n${GREEN}✅ SUPERUSER CRÉÉ AVEC SUCCÈS !${NC}"
echo "Vous pouvez maintenant vous connecter à l'administration Django"
echo "URL: http://78.138.58.185/admin/"

echo -e "\n${YELLOW}5. VÉRIFICATION DU SUPERUSER${NC}"

# Lister les superusers existants
echo "Superusers existants:"
python3 manage.py shell -c "
from django.contrib.auth.models import User
superusers = User.objects.filter(is_superuser=True)
for user in superusers:
    print(f'- {user.username} ({user.email}) - Dernière connexion: {user.last_login}')
"

