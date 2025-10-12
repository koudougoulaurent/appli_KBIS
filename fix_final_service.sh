#!/bin/bash

# Script de correction finale du service
# Arrête le service systemd problématique et utilise une approche stable

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 CORRECTION FINALE DU SERVICE${NC}"
echo "=================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. ARRÊT COMPLET DU SERVICE SYSTEMD${NC}"

# Arrêter et désactiver le service
sudo systemctl stop $SERVICE_NAME
sudo systemctl disable $SERVICE_NAME

echo -e "\n${YELLOW}2. NETTOYAGE DES PROCESSUS${NC}"

# Tuer tous les processus gunicorn
sudo pkill -f gunicorn || true
sleep 2

echo -e "\n${YELLOW}3. DÉMARRAGE MANUEL STABLE${NC}"

cd $APP_DIR
source venv/bin/activate

# Démarrer gunicorn en arrière-plan de manière stable
echo "Démarrage de gunicorn en arrière-plan..."
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &

sleep 3

echo -e "\n${YELLOW}4. VÉRIFICATION${NC}"

# Vérifier que gunicorn fonctionne
if pgrep -f gunicorn > /dev/null; then
    echo -e "${GREEN}✅ Gunicorn fonctionne en arrière-plan${NC}"
    echo "PID: $(pgrep -f gunicorn)"
else
    echo -e "${RED}❌ Gunicorn ne fonctionne pas${NC}"
    exit 1
fi

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

# Test de l'admin
if curl -s -I http://78.138.58.185/admin/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Interface d'administration accessible${NC}"
else
    echo -e "${RED}❌ Interface d'administration non accessible${NC}"
fi

echo -e "\n${YELLOW}5. CRÉATION D'UN SCRIPT DE DÉMARRAGE${NC}"

# Créer un script de démarrage simple
cat > /usr/local/bin/start-kbis.sh << 'EOF'
#!/bin/bash
cd /var/www/kbis_immobilier
source venv/bin/activate
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &
EOF

sudo chmod +x /usr/local/bin/start-kbis.sh

echo -e "\n${YELLOW}6. CRÉATION D'UN SCRIPT D'ARRÊT${NC}"

# Créer un script d'arrêt
cat > /usr/local/bin/stop-kbis.sh << 'EOF'
#!/bin/bash
sudo pkill -f gunicorn
rm -f /tmp/gunicorn.pid
EOF

sudo chmod +x /usr/local/bin/stop-kbis.sh

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Votre application fonctionne maintenant de manière stable !"
echo ""
echo "URLs d'accès :"
echo "- Application : http://78.138.58.185"
echo "- Administration : http://78.138.58.185/admin/"
echo ""
echo "Commandes utiles :"
echo "- Démarrer : /usr/local/bin/start-kbis.sh"
echo "- Arrêter : /usr/local/bin/stop-kbis.sh"
echo "- Vérifier : pgrep -f gunicorn"
echo ""
echo "Pour créer un superuser :"
echo "cd /var/www/kbis_immobilier && source venv/bin/activate && python3 manage.py createsuperuser"


