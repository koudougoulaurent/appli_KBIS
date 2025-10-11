#!/bin/bash

# Script de correction pour le service kbis_immobilier qui échoue
# Résout les problèmes courants après restauration

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 CORRECTION DU SERVICE KBIS_IMMOBILIER${NC}"
echo "============================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. DIAGNOSTIC DU PROBLÈME${NC}"

# Afficher les logs d'erreur
echo "Logs d'erreur du service:"
sudo journalctl -u $SERVICE_NAME --no-pager -l -n 20

echo -e "\n${YELLOW}2. VÉRIFICATION DE L'ENVIRONNEMENT${NC}"

cd $APP_DIR

# Vérifier que le répertoire existe
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Répertoire de l'application non trouvé: $APP_DIR${NC}"
    exit 1
fi

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Environnement virtuel non trouvé${NC}"
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier les dépendances
echo "Vérification des dépendances..."
pip install -r requirements.txt --quiet

echo -e "\n${YELLOW}3. VÉRIFICATION DE LA CONFIGURATION DJANGO${NC}"

# Vérifier la syntaxe Python
echo "Vérification de la syntaxe Python..."
python3 -m py_compile gestion_immobiliere/settings.py 2>&1 || {
    echo -e "${RED}❌ Erreur de syntaxe dans settings.py${NC}"
    
    # Corriger les problèmes d'indentation
    echo "Correction des problèmes d'indentation..."
    sed -i 's/^    CSRF_COOKIE_SECURE/        CSRF_COOKIE_SECURE/' gestion_immobiliere/settings.py
    sed -i 's/^    SESSION_COOKIE_SECURE/        SESSION_COOKIE_SECURE/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_SSL_REDIRECT/        SECURE_SSL_REDIRECT/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_BROWSER_XSS_FILTER/        SECURE_BROWSER_XSS_FILTER/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_CONTENT_TYPE_NOSNIFF/        SECURE_CONTENT_TYPE_NOSNIFF/' gestion_immobiliere/settings.py
    sed -i 's/^    X_FRAME_OPTIONS/        X_FRAME_OPTIONS/' gestion_immobiliere/settings.py
    
    echo "Vérification après correction..."
    python3 -m py_compile gestion_immobiliere/settings.py
}

# Vérifier la configuration Django
echo "Vérification de la configuration Django..."
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

echo -e "\n${YELLOW}4. VÉRIFICATION DES PERMISSIONS${NC}"

# Corriger les permissions
echo "Correction des permissions..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod +x $APP_DIR/venv/bin/*

echo -e "\n${YELLOW}5. TEST MANUEL DE GUNICORN${NC}"

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

echo -e "\n${YELLOW}6. RECONFIGURATION DU SERVICE SYSTEMD${NC}"

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

echo -e "\n${YELLOW}7. REDÉMARRAGE DU SERVICE${NC}"

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

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Votre application devrait maintenant être accessible sur:"
echo "http://78.138.58.185"

