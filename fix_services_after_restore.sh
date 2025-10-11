#!/bin/bash

# Script de correction rapide après restauration VPS
# Corrige l'erreur 502 en redémarrant les services

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 CORRECTION RAPIDE APRÈS RESTAURATION VPS${NC}"
echo "================================================"

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. DIAGNOSTIC INITIAL${NC}"
echo "Vérification de l'état des services..."

# Vérifier l'état des services
echo "État de nginx:"
sudo systemctl is-active nginx || echo "nginx inactif"

echo "État de $SERVICE_NAME:"
sudo systemctl is-active $SERVICE_NAME || echo "$SERVICE_NAME inactif"

echo -e "\n${YELLOW}2. VÉRIFICATION DES FICHIERS CRITIQUES${NC}"

# Vérifier que l'application existe
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Répertoire de l'application non trouvé: $APP_DIR${NC}"
    exit 1
fi

cd $APP_DIR

# Vérifier les fichiers essentiels
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ manage.py non trouvé${NC}"
    exit 1
fi

if [ ! -f "gestion_immobiliere/settings.py" ]; then
    echo -e "${RED}❌ settings.py non trouvé${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Fichiers essentiels trouvés${NC}"

echo -e "\n${YELLOW}3. VÉRIFICATION DE LA SYNTAXE PYTHON${NC}"

# Vérifier la syntaxe Python
python3 -m py_compile gestion_immobiliere/settings.py 2>&1 || {
    echo -e "${RED}❌ Erreur de syntaxe dans settings.py${NC}"
    echo "Correction automatique..."
    
    # Corriger les problèmes d'indentation courants
    sed -i 's/^    CSRF_COOKIE_SECURE/        CSRF_COOKIE_SECURE/' gestion_immobiliere/settings.py
    sed -i 's/^    SESSION_COOKIE_SECURE/        SESSION_COOKIE_SECURE/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_SSL_REDIRECT/        SECURE_SSL_REDIRECT/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_BROWSER_XSS_FILTER/        SECURE_BROWSER_XSS_FILTER/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_CONTENT_TYPE_NOSNIFF/        SECURE_CONTENT_TYPE_NOSNIFF/' gestion_immobiliere/settings.py
    sed -i 's/^    X_FRAME_OPTIONS/        X_FRAME_OPTIONS/' gestion_immobiliere/settings.py
    
    echo "Vérification après correction..."
    python3 -m py_compile gestion_immobiliere/settings.py
}

echo -e "\n${YELLOW}4. REDÉMARRAGE DES SERVICES${NC}"

# Arrêter les services
echo "Arrêt des services..."
sudo systemctl stop nginx 2>/dev/null || true
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Attendre un peu
sleep 2

# Redémarrer le service Django
echo "Redémarrage de $SERVICE_NAME..."
sudo systemctl start $SERVICE_NAME
sleep 3

# Vérifier que le service Django fonctionne
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ Service $SERVICE_NAME démarré${NC}"
else
    echo -e "${RED}❌ Échec du démarrage de $SERVICE_NAME${NC}"
    echo "Logs du service:"
    sudo journalctl -u $SERVICE_NAME --no-pager -l -n 20
    exit 1
fi

# Redémarrer nginx
echo "Redémarrage de nginx..."
sudo systemctl start nginx
sleep 2

# Vérifier que nginx fonctionne
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Service nginx démarré${NC}"
else
    echo -e "${RED}❌ Échec du démarrage de nginx${NC}"
    echo "Logs de nginx:"
    sudo journalctl -u nginx --no-pager -l -n 20
    exit 1
fi

echo -e "\n${YELLOW}5. VÉRIFICATION DE LA CONNECTIVITÉ${NC}"

# Tester la connectivité interne
echo "Test de connectivité interne..."
if curl -s -I http://127.0.0.1:8000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Gunicorn répond sur le port 8000${NC}"
else
    echo -e "${RED}❌ Gunicorn ne répond pas sur le port 8000${NC}"
    echo "Vérification des processus:"
    ps aux | grep gunicorn || echo "Aucun processus gunicorn trouvé"
fi

# Tester la connectivité externe
echo "Test de connectivité externe..."
if curl -s -I http://78.138.58.185 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Application accessible via nginx${NC}"
else
    echo -e "${RED}❌ Application non accessible via nginx${NC}"
    echo "Vérification de la configuration nginx:"
    sudo nginx -t
fi

echo -e "\n${YELLOW}6. COLLECTE DES FICHIERS STATIQUES${NC}"
python3 manage.py collectstatic --noinput

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Votre application devrait maintenant être accessible sur:"
echo "http://78.138.58.185"

echo -e "\n${YELLOW}État final des services:${NC}"
sudo systemctl status $SERVICE_NAME --no-pager -l
sudo systemctl status nginx --no-pager -l

