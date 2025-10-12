#!/bin/bash

# Script de correction du service en boucle de redémarrage
# Résout le problème d'auto-restart constant

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 CORRECTION DU SERVICE EN BOUCLE DE REDÉMARRAGE${NC}"
echo "====================================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. ARRÊT DU SERVICE PROBLÉMATIQUE${NC}"

# Arrêter le service qui redémarre en boucle
sudo systemctl stop $SERVICE_NAME
sudo systemctl disable $SERVICE_NAME

echo -e "\n${YELLOW}2. NETTOYAGE DES PROCESSUS EXISTANTS${NC}"

# Tuer tous les processus gunicorn existants
sudo pkill -f gunicorn || true
sleep 2

# Vérifier qu'aucun processus n'écoute sur le port 8000
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "Arrêt des processus sur le port 8000..."
    sudo fuser -k 8000/tcp || true
    sleep 2
fi

echo -e "\n${YELLOW}3. VÉRIFICATION DE L'APPLICATION${NC}"

cd $APP_DIR
source venv/bin/activate

# Vérifier la configuration Django
echo "Vérification de la configuration Django..."
python3 manage.py check --deploy

echo -e "\n${YELLOW}4. TEST MANUEL DE GUNICORN${NC}"

# Tester gunicorn manuellement
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

echo -e "\n${YELLOW}5. RECONFIGURATION DU SERVICE SYSTEMD${NC}"

# Créer un nouveau service systemd plus robuste
cat > /tmp/kbis_immobilier.service << 'EOF'
[Unit]
Description=KBIS Immobilier Gunicorn daemon
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/kbis_immobilier
Environment="PATH=/var/www/kbis_immobilier/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings"
ExecStart=/var/www/kbis_immobilier/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kbis_immobilier

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/kbis_immobilier.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "\n${YELLOW}6. CORRECTION DES PERMISSIONS${NC}"

# Corriger les permissions
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod +x $APP_DIR/venv/bin/*

echo -e "\n${YELLOW}7. DÉMARRAGE DU SERVICE${NC}"

# Activer et démarrer le service
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Attendre un peu
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

echo -e "\n${YELLOW}8. VÉRIFICATION FINALE${NC}"

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

# Test spécifique de l'admin
echo -e "\nTest de l'admin:"
if curl -s -I http://78.138.58.185/admin/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Interface d'administration accessible${NC}"
else
    echo -e "${RED}❌ Interface d'administration non accessible${NC}"
fi

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Votre application devrait maintenant être stable et accessible sur:"
echo "http://78.138.58.185"
echo "Interface d'administration: http://78.138.58.185/admin/"


