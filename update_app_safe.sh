#!/bin/bash

# Script de mise à jour sécurisée de l'application KBIS
# Préserve toutes les configurations et données

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 MISE À JOUR SÉCURISÉE DE L'APPLICATION KBIS${NC}"
echo "==============================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"
DATE=$(date +%Y%m%d_%H%M%S)
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. VÉRIFICATION DE L'ÉTAT ACTUEL${NC}"

# Vérifier que l'application existe
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Répertoire de l'application non trouvé: $APP_DIR${NC}"
    exit 1
fi

cd $APP_DIR

# Vérifier l'état de git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Ce n'est pas un dépôt Git${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Application trouvée${NC}"

echo -e "\n${YELLOW}2. SAUVEGARDE DE LA CONFIGURATION${NC}"

# Créer le répertoire de sauvegarde
sudo mkdir -p $BACKUP_DIR

# Sauvegarder les fichiers de configuration critiques
echo "Sauvegarde des configurations..."
sudo cp -r $APP_DIR/gestion_immobiliere/settings.py $BACKUP_DIR/settings_$DATE.py
sudo cp -r /etc/nginx/sites-available/kbis_immobilier $BACKUP_DIR/nginx_$DATE.conf
sudo cp -r /etc/systemd/system/kbis_immobilier.service $BACKUP_DIR/systemd_$DATE.service 2>/dev/null || true

# Sauvegarder la base de données
echo "Sauvegarde de la base de données..."
source venv/bin/activate
python3 manage.py dumpdata > $BACKUP_DIR/database_$DATE.json

echo -e "${GREEN}✅ Sauvegarde terminée${NC}"

echo -e "\n${YELLOW}3. ARRÊT DES SERVICES${NC}"

# Arrêter les services
sudo pkill -f gunicorn || true
sleep 3

echo -e "\n${YELLOW}4. MISE À JOUR DU CODE${NC}"

# Sauvegarder les modifications locales
git stash push -m "Sauvegarde avant mise à jour $DATE"

# Récupérer les dernières modifications
echo "Récupération des dernières modifications..."
git fetch origin

# Voir les commits disponibles
echo "Commits disponibles:"
git log --oneline origin/main -10

# Demander confirmation
echo -e "\n${YELLOW}Voulez-vous continuer avec la mise à jour ? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Mise à jour annulée"
    git stash pop
    exit 0
fi

# Mettre à jour vers la dernière version
git pull origin main

echo -e "${GREEN}✅ Code mis à jour${NC}"

echo -e "\n${YELLOW}5. RESTAURATION DE LA CONFIGURATION${NC}"

# Restaurer les fichiers de configuration
echo "Restauration des configurations..."
cp $BACKUP_DIR/settings_$DATE.py gestion_immobiliere/settings.py
sudo cp $BACKUP_DIR/nginx_$DATE.conf /etc/nginx/sites-available/kbis_immobilier

# Restaurer les permissions
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

echo -e "${GREEN}✅ Configuration restaurée${NC}"

echo -e "\n${YELLOW}6. MISE À JOUR DES DÉPENDANCES${NC}"

# Activer l'environnement virtuel
source venv/bin/activate

# Mettre à jour les dépendances
echo "Mise à jour des dépendances..."
pip install -r requirements.txt --upgrade

echo -e "${GREEN}✅ Dépendances mises à jour${NC}"

echo -e "\n${YELLOW}7. MIGRATIONS DE BASE DE DONNÉES${NC}"

# Appliquer les migrations
echo "Application des migrations..."
python3 manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

echo -e "${GREEN}✅ Migrations appliquées${NC}"

echo -e "\n${YELLOW}8. REDÉMARRAGE DES SERVICES${NC}"

# Redémarrer gunicorn
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &

sleep 3

# Redémarrer nginx
sudo systemctl restart nginx

echo -e "${GREEN}✅ Services redémarrés${NC}"

echo -e "\n${YELLOW}9. VÉRIFICATION FINALE${NC}"

# Vérifier que gunicorn fonctionne
if pgrep -f gunicorn > /dev/null; then
    echo -e "${GREEN}✅ Gunicorn fonctionne${NC}"
else
    echo -e "${RED}❌ Gunicorn ne fonctionne pas${NC}"
    echo "Restauration de la sauvegarde..."
    git reset --hard HEAD~1
    git stash pop
    exit 1
fi

# Vérifier nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx fonctionne${NC}"
else
    echo -e "${RED}❌ Nginx ne fonctionne pas${NC}"
    exit 1
fi

# Test de connectivité
echo "Test de connectivité..."
if curl -s -I https://78.138.58.185 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Application accessible${NC}"
else
    echo -e "${RED}❌ Application non accessible${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS !${NC}"
echo "Votre application a été mise à jour sans altérer les configurations."
echo ""
echo "Sauvegardes créées :"
echo "- Configuration : $BACKUP_DIR/settings_$DATE.py"
echo "- Nginx : $BACKUP_DIR/nginx_$DATE.conf"
echo "- Base de données : $BACKUP_DIR/database_$DATE.json"
echo ""
echo "URLs d'accès :"
echo "- Application : https://78.138.58.185"
echo "- Administration : https://78.138.58.185/admin/"

