#!/bin/bash

# Script de correction pour Django et Gunicorn après restauration
# Résout les problèmes d'installation et de configuration

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 CORRECTION DJANGO ET GUNICORN${NC}"
echo "====================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. INSTALLATION DES DÉPENDANCES${NC}"

cd $APP_DIR

# Activer l'environnement virtuel
source venv/bin/activate

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Vérifier Django
echo "Vérification de Django..."
python3 -c "import django; print('Django version:', django.get_version())" || {
    echo -e "${RED}❌ Django non installé correctement${NC}"
    pip install django
}

echo -e "\n${YELLOW}2. VÉRIFICATION DE LA CONFIGURATION DJANGO${NC}"

# Vérifier la configuration
python3 manage.py check --deploy 2>&1 || {
    echo -e "${RED}❌ Problème de configuration Django${NC}"
    
    # Corriger les références
    echo "Correction des références..."
    find . -name "*.py" -exec sed -i 's/gestimmob/gestion_immobiliere/g' {} \;
    find . -name "*.py" -exec sed -i 's/settings_simple/settings/g' {} \;
    find . -name "*.py" -exec sed -i 's/settings_production/settings/g' {} \;
    
    # Vérifier wsgi.py
    grep -q "gestion_immobiliere.settings" gestion_immobiliere/wsgi.py || {
        echo "Correction de wsgi.py..."
        sed -i 's/DJANGO_SETTINGS_MODULE.*/DJANGO_SETTINGS_MODULE", "gestion_immobiliere.settings")/' gestion_immobiliere/wsgi.py
    }
    
    # Vérifier manage.py
    grep -q "gestion_immobiliere.settings" manage.py || {
        echo "Correction de manage.py..."
        sed -i 's/DJANGO_SETTINGS_MODULE.*/DJANGO_SETTINGS_MODULE", "gestion_immobiliere.settings")/' manage.py
    }
}

echo -e "\n${YELLOW}3. TEST DE GUNICORN${NC}"

# Tester gunicorn
echo "Test de gunicorn..."
timeout 10s gunicorn --workers 3 --bind 127.0.0.1:8000 gestion_immobiliere.wsgi:application &
GUNICORN_PID=$!

sleep 3

# Vérifier si gunicorn répond
if curl -s -I http://127.0.0.1:8000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Gunicorn fonctionne correctement${NC}"
    kill $GUNICORN_PID 2>/dev/null || true
else
    echo -e "${RED}❌ Gunicorn ne répond pas${NC}"
    kill $GUNICORN_PID 2>/dev/null || true
    exit 1
fi

echo -e "\n${YELLOW}4. CONFIGURATION DU SERVICE SYSTEMD${NC}"

# Créer le service systemd correct
cat > /tmp/kbis_immobilier.service << 'EOF'
[Unit]
Description=KBIS Immobilier Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/kbis_immobilier
Environment="PATH=/var/www/kbis_immobilier/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings"
ExecStart=/var/www/kbis_immobilier/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/kbis_immobilier.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "\n${YELLOW}5. CORRECTION DES PERMISSIONS${NC}"

# Corriger les permissions
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod +x $APP_DIR/venv/bin/*

echo -e "\n${YELLOW}6. REDÉMARRAGE DU SERVICE${NC}"

# Redémarrer le service
sudo systemctl restart $SERVICE_NAME
sleep 5

# Vérifier le statut
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ Service $SERVICE_NAME démarré avec succès${NC}"
else
    echo -e "${RED}❌ Échec du démarrage du service${NC}"
    echo "Logs d'erreur:"
    sudo journalctl -u $SERVICE_NAME --no-pager -l -n 10
    exit 1
fi

echo -e "\n${YELLOW}7. VÉRIFICATION FINALE${NC}"

# Vérifier les ports
echo "Ports ouverts:"
netstat -tlnp | grep -E ":(80|8000) "

# Test de connectivité
echo -e "\nTest de connectivité:"
if curl -s -I http://127.0.0.1:8000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Gunicorn répond sur le port 8000${NC}"
else
    echo -e "${RED}❌ Gunicorn ne répond pas${NC}"
fi

if curl -s -I http://78.138.58.185 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Application accessible via nginx${NC}"
else
    echo -e "${RED}❌ Application non accessible via nginx${NC}"
fi

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Votre application devrait maintenant être accessible sur:"
echo "http://78.138.58.185"

