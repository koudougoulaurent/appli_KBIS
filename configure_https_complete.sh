#!/bin/bash

# Script de configuration HTTPS complète avec Let's Encrypt
# Configure SSL/TLS pour l'application KBIS

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔒 CONFIGURATION HTTPS COMPLÈTE${NC}"
echo "=================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"
DOMAIN="78.138.58.185"  # Votre IP publique
EMAIL="kdg1@gmail.com"  # Email pour Let's Encrypt

echo -e "\n${YELLOW}1. INSTALLATION DE CERTBOT${NC}"

# Mettre à jour le système
sudo apt update

# Installer certbot et nginx plugin
sudo apt install -y certbot python3-certbot-nginx

echo -e "\n${YELLOW}2. CONFIGURATION NGINX POUR HTTPS${NC}"

# Créer la configuration nginx pour HTTPS
cat > /tmp/kbis_immobilier_https << 'EOF'
server {
    listen 80;
    server_name 78.138.58.185;
    
    # Redirection vers HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 78.138.58.185;

    # Certificats SSL (seront générés par certbot)
    ssl_certificate /etc/letsencrypt/live/78.138.58.185/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/78.138.58.185/privkey.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Augmenter la limite de taille des requêtes
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    location /static/ {
        alias /var/www/kbis_immobilier/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/kbis_immobilier/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_redirect off;
    }
}
EOF

# Sauvegarder l'ancienne configuration
sudo cp /etc/nginx/sites-available/kbis_immobilier /etc/nginx/sites-available/kbis_immobilier.backup 2>/dev/null || true

# Installer la nouvelle configuration
sudo mv /tmp/kbis_immobilier_https /etc/nginx/sites-available/kbis_immobilier
sudo rm -f /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/kbis_immobilier /etc/nginx/sites-enabled/

echo -e "\n${YELLOW}3. CONFIGURATION DJANGO POUR HTTPS${NC}"

cd $APP_DIR
source venv/bin/activate

# Sauvegarder settings.py
cp gestion_immobiliere/settings.py gestion_immobiliere/settings.py.backup

# Créer un script pour configurer Django pour HTTPS
cat > /tmp/configure_django_https.py << 'EOF'
import re

# Lire le fichier settings.py
with open('gestion_immobiliere/settings.py', 'r') as f:
    content = f.read()

# Configuration HTTPS pour Django
https_settings = '''
# Configuration HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_REDIRECT_EXEMPT = []

# Configuration pour les formulaires HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://78.138.58.185',
    'https://localhost',
    'http://78.138.58.185',  # Pour la transition
    'http://localhost'
]
ALLOWED_HOSTS = ['78.138.58.185', 'localhost', '127.0.0.1']

# Configuration des cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
'''

# Supprimer les anciens paramètres HTTPS
https_patterns = [
    r'^SECURE_SSL_REDIRECT.*\n',
    r'^SECURE_HSTS_SECONDS.*\n',
    r'^SECURE_HSTS_INCLUDE_SUBDOMAINS.*\n',
    r'^SECURE_HSTS_PRELOAD.*\n',
    r'^SECURE_PROXY_SSL_HEADER.*\n',
    r'^SECURE_BROWSER_XSS_FILTER.*\n',
    r'^SECURE_CONTENT_TYPE_NOSNIFF.*\n',
    r'^SECURE_REFERRER_POLICY.*\n',
    r'^SESSION_COOKIE_SECURE.*\n',
    r'^CSRF_COOKIE_SECURE.*\n',
    r'^SECURE_REDIRECT_EXEMPT.*\n',
    r'^CSRF_TRUSTED_ORIGINS.*\n',
    r'^ALLOWED_HOSTS.*\n',
    r'^SESSION_COOKIE_HTTPONLY.*\n',
    r'^CSRF_COOKIE_HTTPONLY.*\n',
    r'^SESSION_COOKIE_SAMESITE.*\n',
    r'^CSRF_COOKIE_SAMESITE.*\n',
]

for pattern in https_patterns:
    content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Ajouter la nouvelle configuration
content += https_settings

# Écrire le fichier modifié
with open('gestion_immobiliere/settings.py', 'w') as f:
    f.write(content)

print("Configuration Django pour HTTPS terminée")
EOF

python3 /tmp/configure_django_https.py

echo -e "\n${YELLOW}4. VÉRIFICATION DE LA SYNTAXE${NC}"

# Vérifier la syntaxe Python
python3 -m py_compile gestion_immobiliere/settings.py

# Vérifier la configuration nginx
sudo nginx -t

echo -e "\n${YELLOW}5. GÉNÉRATION DU CERTIFICAT SSL${NC}"

# Générer le certificat SSL avec Let's Encrypt
echo "Génération du certificat SSL pour $DOMAIN..."
sudo certbot certonly --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect

echo -e "\n${YELLOW}6. REDÉMARRAGE DES SERVICES${NC}"

# Arrêter gunicorn
sudo pkill -f gunicorn || true
sleep 2

# Redémarrer gunicorn
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &

sleep 3

# Redémarrer nginx
sudo systemctl restart nginx

echo -e "\n${YELLOW}7. VÉRIFICATION FINALE${NC}"

# Vérifier que gunicorn fonctionne
if pgrep -f gunicorn > /dev/null; then
    echo -e "${GREEN}✅ Gunicorn fonctionne${NC}"
else
    echo -e "${RED}❌ Gunicorn ne fonctionne pas${NC}"
fi

# Vérifier nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx fonctionne${NC}"
else
    echo -e "${RED}❌ Nginx ne fonctionne pas${NC}"
fi

# Test HTTP (doit rediriger vers HTTPS)
echo "Test de redirection HTTP vers HTTPS:"
curl -I http://$DOMAIN 2>/dev/null | head -3

# Test HTTPS
echo -e "\nTest HTTPS:"
if curl -s -I https://$DOMAIN >/dev/null 2>&1; then
    echo -e "${GREEN}✅ HTTPS fonctionne${NC}"
else
    echo -e "${RED}❌ HTTPS ne fonctionne pas${NC}"
fi

# Test de l'admin HTTPS
echo -e "\nTest de l'administration HTTPS:"
if curl -s -I https://$DOMAIN/admin/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Interface d'administration HTTPS accessible${NC}"
else
    echo -e "${RED}❌ Interface d'administration HTTPS non accessible${NC}"
fi

echo -e "\n${GREEN}🎉 CONFIGURATION HTTPS TERMINÉE !${NC}"
echo "Votre application est maintenant sécurisée avec HTTPS !"
echo ""
echo "URLs d'accès :"
echo "- Application HTTPS : https://$DOMAIN"
echo "- Administration HTTPS : https://$DOMAIN/admin/"
echo "- Redirection automatique HTTP → HTTPS"
echo ""
echo "Le certificat SSL sera renouvelé automatiquement tous les 90 jours."
echo ""
echo "Pour vérifier le certificat :"
echo "sudo certbot certificates"
echo ""
echo "Pour renouveler manuellement :"
echo "sudo certbot renew"

