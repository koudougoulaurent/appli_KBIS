#!/bin/bash

# Script de retour en arrière (rollback) de l'application
# Restaure une version précédente en cas de problème

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}⏪ RETOUR EN ARRIÈRE (ROLLBACK) DE L'APPLICATION${NC}"
echo "============================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"

echo -e "\n${YELLOW}1. VÉRIFICATION DES SAUVEGARDES DISPONIBLES${NC}"

# Lister les sauvegardes disponibles
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ Aucune sauvegarde trouvée dans $BACKUP_DIR${NC}"
    exit 1
fi

echo "Sauvegardes disponibles :"
ls -la $BACKUP_DIR/ | grep -E "(settings_|nginx_|database_)" | head -10

echo -e "\n${YELLOW}2. SÉLECTION DE LA SAUVEGARDE${NC}"

# Demander la date de sauvegarde
echo -e "Entrez la date de sauvegarde à restaurer (format: YYYYMMDD_HHMMSS) ou 'latest' pour la plus récente:"
read -r backup_date

if [ "$backup_date" = "latest" ]; then
    # Trouver la sauvegarde la plus récente
    backup_date=$(ls -t $BACKUP_DIR/settings_*.py 2>/dev/null | head -1 | sed 's/.*settings_\(.*\)\.py/\1/')
    if [ -z "$backup_date" ]; then
        echo -e "${RED}❌ Aucune sauvegarde trouvée${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Sauvegarde la plus récente trouvée: $backup_date${NC}"
fi

# Vérifier que la sauvegarde existe
if [ ! -f "$BACKUP_DIR/settings_$backup_date.py" ]; then
    echo -e "${RED}❌ Sauvegarde non trouvée: $backup_date${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Sauvegarde trouvée: $backup_date${NC}"

echo -e "\n${YELLOW}3. ARRÊT DES SERVICES${NC}"

# Arrêter les services
sudo pkill -f gunicorn || true
sleep 3

echo -e "\n${YELLOW}4. RESTAURATION DE LA CONFIGURATION${NC}"

cd $APP_DIR

# Restaurer les fichiers de configuration
echo "Restauration des configurations..."
cp $BACKUP_DIR/settings_$backup_date.py gestion_immobiliere/settings.py
sudo cp $BACKUP_DIR/nginx_$backup_date.conf /etc/nginx/sites-available/kbis_immobilier

# Restaurer les permissions
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

echo -e "${GREEN}✅ Configuration restaurée${NC}"

echo -e "\n${YELLOW}5. RESTAURATION DE LA BASE DE DONNÉES${NC}"

# Activer l'environnement virtuel
source venv/bin/activate

# Sauvegarder la base de données actuelle
echo "Sauvegarde de la base de données actuelle..."
python3 manage.py dumpdata > $BACKUP_DIR/database_before_rollback_$(date +%Y%m%d_%H%M%S).json

# Restaurer la base de données
echo "Restauration de la base de données..."
python3 manage.py loaddata $BACKUP_DIR/database_$backup_date.json

echo -e "${GREEN}✅ Base de données restaurée${NC}"

echo -e "\n${YELLOW}6. REDÉMARRAGE DES SERVICES${NC}"

# Redémarrer gunicorn
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &

sleep 3

# Redémarrer nginx
sudo systemctl restart nginx

echo -e "${GREEN}✅ Services redémarrés${NC}"

echo -e "\n${YELLOW}7. VÉRIFICATION FINALE${NC}"

# Vérifier que gunicorn fonctionne
if pgrep -f gunicorn > /dev/null; then
    echo -e "${GREEN}✅ Gunicorn fonctionne${NC}"
else
    echo -e "${RED}❌ Gunicorn ne fonctionne pas${NC}"
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

echo -e "\n${GREEN}🎉 ROLLBACK TERMINÉ AVEC SUCCÈS !${NC}"
echo "Votre application a été restaurée à la sauvegarde du $backup_date"
echo ""
echo "Sauvegardes créées :"
echo "- Base de données avant rollback : $BACKUP_DIR/database_before_rollback_$(date +%Y%m%d_%H%M%S).json"
echo ""
echo "URLs d'accès :"
echo "- Application : https://78.138.58.185"
echo "- Administration : https://78.138.58.185/admin/"

