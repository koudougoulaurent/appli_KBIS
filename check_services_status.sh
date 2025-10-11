#!/bin/bash

# Script de vérification rapide des services
# Diagnostique l'état des services après erreur 502

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 VÉRIFICATION RAPIDE DES SERVICES${NC}"
echo "====================================="

# Variables
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. ÉTAT DES SERVICES${NC}"

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

echo -e "\n${YELLOW}3. LOGS RÉCENTS${NC}"

# Logs du service Django
echo "Dernières erreurs $SERVICE_NAME:"
sudo journalctl -u $SERVICE_NAME --no-pager -l -n 5 2>/dev/null || echo "Aucun log trouvé"

# Logs nginx
echo -e "\nDernières erreurs nginx:"
sudo tail -n 3 /var/log/nginx/error.log 2>/dev/null || echo "Aucun log nginx trouvé"

echo -e "\n${YELLOW}4. TEST DE CONNECTIVITÉ${NC}"

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

echo -e "\n${YELLOW}5. ACTIONS RECOMMANDÉES${NC}"

if ! sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${RED}→ Redémarrer le service Django:${NC}"
    echo "  sudo systemctl restart $SERVICE_NAME"
    echo "  sudo systemctl status $SERVICE_NAME"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo -e "${RED}→ Le service Django ne répond pas sur le port 8000${NC}"
    echo "  Vérifier les logs: sudo journalctl -u $SERVICE_NAME -f"
fi

echo -e "\n${BLUE}💡 SOLUTION RAPIDE:${NC}"
echo "sudo systemctl restart $SERVICE_NAME"
echo "sudo systemctl restart nginx"

