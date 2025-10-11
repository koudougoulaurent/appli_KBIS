#!/bin/bash

# Script de diagnostic rapide pour l'erreur 502
# Identifie rapidement le problème après restauration

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 DIAGNOSTIC RAPIDE ERREUR 502${NC}"
echo "=================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. VÉRIFICATION DES SERVICES${NC}"

# Vérifier nginx
echo -n "nginx: "
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ ACTIF${NC}"
else
    echo -e "${RED}❌ INACTIF${NC}"
fi

# Vérifier le service Django
echo -n "$SERVICE_NAME: "
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ ACTIF${NC}"
else
    echo -e "${RED}❌ INACTIF${NC}"
fi

echo -e "\n${YELLOW}2. VÉRIFICATION DES PORTS${NC}"

# Vérifier le port 8000 (Gunicorn)
echo -n "Port 8000 (Gunicorn): "
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo -e "${GREEN}✅ ÉCOUTE${NC}"
else
    echo -e "${RED}❌ FERMÉ${NC}"
fi

# Vérifier le port 80 (Nginx)
echo -n "Port 80 (Nginx): "
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${GREEN}✅ ÉCOUTE${NC}"
else
    echo -e "${RED}❌ FERMÉ${NC}"
fi

echo -e "\n${YELLOW}3. TEST DE CONNECTIVITÉ${NC}"

# Test interne
echo -n "Test interne (127.0.0.1:8000): "
if curl -s -I http://127.0.0.1:8000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ RÉPOND${NC}"
else
    echo -e "${RED}❌ NE RÉPOND PAS${NC}"
fi

# Test externe
echo -n "Test externe (78.138.58.185): "
if curl -s -I http://78.138.58.185 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ RÉPOND${NC}"
else
    echo -e "${RED}❌ NE RÉPOND PAS${NC}"
fi

echo -e "\n${YELLOW}4. VÉRIFICATION DES LOGS${NC}"

# Logs nginx
echo "Dernières erreurs nginx:"
sudo tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "Aucun log nginx trouvé"

# Logs du service Django
echo -e "\nDernières erreurs $SERVICE_NAME:"
sudo journalctl -u $SERVICE_NAME --no-pager -l -n 5 2>/dev/null || echo "Aucun log du service trouvé"

echo -e "\n${YELLOW}5. RECOMMANDATIONS${NC}"

# Analyser les résultats et donner des recommandations
if ! sudo systemctl is-active --quiet nginx; then
    echo -e "${RED}→ Démarrer nginx: sudo systemctl start nginx${NC}"
fi

if ! sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${RED}→ Démarrer $SERVICE_NAME: sudo systemctl start $SERVICE_NAME${NC}"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo -e "${RED}→ Le service Django ne semble pas écouter sur le port 8000${NC}"
    echo -e "${RED}→ Vérifier la configuration du service systemd${NC}"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${RED}→ Nginx ne semble pas écouter sur le port 80${NC}"
    echo -e "${RED}→ Vérifier la configuration nginx${NC}"
fi

echo -e "\n${BLUE}💡 SOLUTION RAPIDE:${NC}"
echo "Exécutez: bash fix_services_after_restore.sh"

