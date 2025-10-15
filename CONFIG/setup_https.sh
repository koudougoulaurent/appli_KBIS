#!/bin/bash

# Script de configuration HTTPS pour KBIS Immobilier
# Utilise Let's Encrypt avec Certbot

set -e

# Variables
DOMAIN=""
EMAIL=""

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Demander le domaine et l'email
read -p "Entrez votre domaine (ex: kbis.votre-domaine.com): " DOMAIN
read -p "Entrez votre email pour Let's Encrypt: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    log_error "Le domaine et l'email sont requis"
    exit 1
fi

log_info "Configuration HTTPS pour le domaine: $DOMAIN"

# Mise à jour de la configuration Nginx
log_info "Mise à jour de la configuration Nginx..."
sudo tee /etc/nginx/sites-available/kbis-immobilier > /dev/null << EOF
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirection vers HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Configuration SSL (sera mise à jour par Certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de sécurité
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Taille maximale des uploads
    client_max_body_size 100M;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Fichiers statiques
    location /static/ {
        alias /home/kbis/appli_KBIS/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média
    location /media/ {
        alias /home/kbis/appli_KBIS/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Application Django
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # Logs
    access_log /var/log/nginx/kbis_access.log;
    error_log /var/log/nginx/kbis_error.log;
}
EOF

# Test de la configuration Nginx
sudo nginx -t

# Redémarrage de Nginx
sudo systemctl restart nginx

# Installation du certificat SSL
log_info "Installation du certificat SSL avec Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# Mise à jour de la configuration Django pour HTTPS
log_info "Mise à jour de la configuration Django pour HTTPS..."
cd /home/kbis/appli_KBIS
source venv/bin/activate

# Mise à jour du fichier .env
sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' .env
sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN,www.$DOMAIN/" .env

# Redémarrage de l'application
sudo systemctl restart kbis-immobilier

# Configuration du renouvellement automatique
log_info "Configuration du renouvellement automatique..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

log_success "Configuration HTTPS terminée !"
log_info "Votre application est maintenant accessible sur: https://$DOMAIN"
log_info "Admin: https://$DOMAIN/admin (admin/admin123)"
