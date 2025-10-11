#!/bin/bash

# Script de déploiement depuis un commit spécifique
# Permet de déployer une version précise sans altérer les configurations

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 DÉPLOIEMENT DEPUIS UN COMMIT SPÉCIFIQUE${NC}"
echo "============================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"
DATE=$(date +%Y%m%d_%H%M%S)

echo -e "\n${YELLOW}1. VÉRIFICATION DE L'ÉTAT ACTUEL${NC}"

cd $APP_DIR

# Vérifier l'état de git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Ce n'est pas un dépôt Git${NC}"
    exit 1
fi

# Afficher les commits récents
echo "Commits récents disponibles:"
git log --oneline -10

echo -e "\n${YELLOW}2. SÉLECTION DU COMMIT${NC}"

# Demander le hash du commit
echo -e "Entrez le hash du commit à déployer (ou 'main' pour la dernière version):"
read -r commit_hash

if [ "$commit_hash" = "main" ] || [ "$commit_hash" = "master" ]; then
    commit_hash="origin/main"
fi

# Vérifier que le commit existe
if ! git cat-file -e "$commit_hash" 2>/dev/null; then
    echo -e "${RED}❌ Commit non trouvé: $commit_hash${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Commit trouvé: $commit_hash${NC}"

echo -e "\n${YELLOW}3. SAUVEGARDE DE LA CONFIGURATION${NC}"

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

echo -e "\n${YELLOW}4. ARRÊT DES SERVICES${NC}"

# Arrêter les services
sudo pkill -f gunicorn || true
sleep 3

echo -e "\n${YELLOW}5. DÉPLOIEMENT DU COMMIT${NC}"

# Sauvegarder les modifications locales
git stash push -m "Sauvegarde avant déploiement $commit_hash $DATE"

# Récupérer les dernières modifications
git fetch origin

# Se déplacer vers le commit spécifié
git checkout $commit_hash

echo -e "${GREEN}✅ Code déployé depuis le commit $commit_hash${NC}"

echo -e "\n${YELLOW}6. RESTAURATION DE LA CONFIGURATION${NC}"

# Restaurer les fichiers de configuration
echo "Restauration des configurations..."
cp $BACKUP_DIR/settings_$DATE.py gestion_immobiliere/settings.py
sudo cp $BACKUP_DIR/nginx_$DATE.conf /etc/nginx/sites-available/kbis_immobilier

# Restaurer les permissions
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

echo -e "${GREEN}✅ Configuration restaurée${NC}"

echo -e "\n${YELLOW}7. MISE À JOUR DES DÉPENDANCES${NC}"

# Activer l'environnement virtuel
source venv/bin/activate

# Mettre à jour les dépendances
echo "Mise à jour des dépendances..."
pip install -r requirements.txt --upgrade

echo -e "${GREEN}✅ Dépendances mises à jour${NC}"

echo -e "\n${YELLOW}8. MIGRATIONS DE BASE DE DONNÉES${NC}"

# Appliquer les migrations
echo "Application des migrations..."
python3 manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

echo -e "${GREEN}✅ Migrations appliquées${NC}"

echo -e "\n${YELLOW}9. REDÉMARRAGE DES SERVICES${NC}"

# Redémarrer gunicorn
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &

sleep 3

# Redémarrer nginx
sudo systemctl restart nginx

echo -e "${GREEN}✅ Services redémarrés${NC}"

echo -e "\n${YELLOW}10. VÉRIFICATION FINALE${NC}"

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

echo -e "\n${GREEN}🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !${NC}"
echo "Votre application a été déployée depuis le commit $commit_hash"
echo "Toutes les configurations ont été préservées."
echo ""
echo "Sauvegardes créées :"
echo "- Configuration : $BACKUP_DIR/settings_$DATE.py"
echo "- Nginx : $BACKUP_DIR/nginx_$DATE.conf"
echo "- Base de données : $BACKUP_DIR/database_$DATE.json"
echo ""
echo "URLs d'accès :"
echo "- Application : https://78.138.58.185"
echo "- Administration : https://78.138.58.185/admin/"

