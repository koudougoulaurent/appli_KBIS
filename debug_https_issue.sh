#!/bin/bash

# Script de débogage pour le problème HTTPS
# Diagnostique pourquoi HTTPS ne fonctionne pas

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 DÉBOGAGE DU PROBLÈME HTTPS${NC}"
echo "================================="

# Variables
DOMAIN="78.138.58.185"

echo -e "\n${YELLOW}1. VÉRIFICATION DES CERTIFICATS${NC}"

# Vérifier que les certificats existent
if [ -f "/etc/ssl/certs/kbis_immobilier.crt" ]; then
    echo -e "${GREEN}✅ Certificat trouvé${NC}"
    ls -la /etc/ssl/certs/kbis_immobilier.crt
else
    echo -e "${RED}❌ Certificat non trouvé${NC}"
fi

if [ -f "/etc/ssl/private/kbis_immobilier.key" ]; then
    echo -e "${GREEN}✅ Clé privée trouvée${NC}"
    ls -la /etc/ssl/private/kbis_immobilier.key
else
    echo -e "${RED}❌ Clé privée non trouvée${NC}"
fi

echo -e "\n${YELLOW}2. VÉRIFICATION DES PORTS${NC}"

# Vérifier les ports ouverts
echo "Ports ouverts:"
netstat -tlnp | grep -E ":(80|443|8000) "

echo -e "\n${YELLOW}3. VÉRIFICATION DE LA CONFIGURATION NGINX${NC}"

# Vérifier la configuration nginx
echo "Configuration nginx active:"
sudo nginx -T | grep -A 20 "server_name $DOMAIN"

echo -e "\n${YELLOW}4. TEST DE CONNECTIVITÉ DÉTAILLÉ${NC}"

# Test HTTP
echo "Test HTTP:"
curl -v http://$DOMAIN 2>&1 | head -10

echo -e "\nTest HTTPS:"
curl -v https://$DOMAIN 2>&1 | head -10

echo -e "\n${YELLOW}5. VÉRIFICATION DES LOGS NGINX${NC}"

# Vérifier les logs nginx
echo "Dernières erreurs nginx:"
sudo tail -n 10 /var/log/nginx/error.log

echo -e "\n${YELLOW}6. TEST DU CERTIFICAT SSL${NC}"

# Tester le certificat
if [ -f "/etc/ssl/certs/kbis_immobilier.crt" ]; then
    echo "Informations du certificat:"
    openssl x509 -in /etc/ssl/certs/kbis_immobilier.crt -text -noout | grep -E "(Subject|Not Before|Not After)"
fi

echo -e "\n${YELLOW}7. VÉRIFICATION DU SERVICE NGINX${NC}"

# Vérifier le statut de nginx
sudo systemctl status nginx --no-pager -l

echo -e "\n${YELLOW}8. CORRECTION AUTOMATIQUE${NC}"

# Vérifier si nginx écoute sur le port 443
if ! netstat -tlnp | grep -q ":443 "; then
    echo -e "${RED}❌ Nginx n'écoute pas sur le port 443${NC}"
    echo "Redémarrage de nginx..."
    sudo systemctl restart nginx
    sleep 3
    
    echo "Vérification après redémarrage:"
    netstat -tlnp | grep -E ":(80|443|8000) "
fi

echo -e "\n${YELLOW}9. TEST FINAL${NC}"

# Test final
echo "Test final HTTPS:"
if curl -s -I https://$DOMAIN >/dev/null 2>&1; then
    echo -e "${GREEN}✅ HTTPS fonctionne maintenant${NC}"
else
    echo -e "${RED}❌ HTTPS ne fonctionne toujours pas${NC}"
    echo "Vérifiez les logs nginx pour plus de détails:"
    echo "sudo tail -f /var/log/nginx/error.log"
fi

