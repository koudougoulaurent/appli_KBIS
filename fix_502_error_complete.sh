#!/bin/bash

# Script de correction complète de l'erreur 502
# Auteur: Assistant IA
# Date: $(date)

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 CORRECTION COMPLÈTE DE L'ERREUR 502${NC}"
echo "================================================"

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "\n${YELLOW}1. ARRÊT DES SERVICES${NC}"
sudo systemctl stop nginx
sudo systemctl stop $SERVICE_NAME

echo -e "\n${YELLOW}2. DIAGNOSTIC DU FICHIER SETTINGS.PY${NC}"
cd $APP_DIR

# Vérifier la syntaxe Python
echo "Vérification de la syntaxe Python..."
python3 -m py_compile gestion_immobiliere/settings.py 2>&1 || {
    echo -e "${RED}❌ Erreur de syntaxe détectée dans settings.py${NC}"
    
    # Afficher les lignes autour de l'erreur
    echo "Lignes autour de la ligne 175:"
    cat -n gestion_immobiliere/settings.py | sed -n '170,180p'
    
    # Corriger automatiquement les problèmes d'indentation
    echo "Correction automatique des problèmes d'indentation..."
    sed -i 's/^    CSRF_COOKIE_SECURE/        CSRF_COOKIE_SECURE/' gestion_immobiliere/settings.py
    sed -i 's/^    SESSION_COOKIE_SECURE/        SESSION_COOKIE_SECURE/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_SSL_REDIRECT/        SECURE_SSL_REDIRECT/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_BROWSER_XSS_FILTER/        SECURE_BROWSER_XSS_FILTER/' gestion_immobiliere/settings.py
    sed -i 's/^    SECURE_CONTENT_TYPE_NOSNIFF/        SECURE_CONTENT_TYPE_NOSNIFF/' gestion_immobiliere/settings.py
    sed -i 's/^    X_FRAME_OPTIONS/        X_FRAME_OPTIONS/' gestion_immobiliere/settings.py
    
    echo "Vérification après correction..."
    python3 -m py_compile gestion_immobiliere/settings.py
}

echo -e "\n${YELLOW}3. VÉRIFICATION DE LA CONFIGURATION DJANGO${NC}"

# Vérifier que Django peut démarrer
echo "Test de démarrage Django..."
python3 manage.py check --deploy 2>&1 || {
    echo -e "${RED}❌ Problème de configuration Django détecté${NC}"
    
    # Corriger les références gestimmob
    echo "Correction des références gestimmob..."
    find . -name "*.py" -exec sed -i 's/gestimmob/gestion_immobiliere/g' {} \;
    find . -name "*.py" -exec sed -i 's/settings_simple/settings/g' {} \;
    find . -name "*.py" -exec sed -i 's/settings_production/settings/g' {} \;
    
    # Vérifier wsgi.py
    echo "Vérification de wsgi.py..."
    grep -q "gestion_immobiliere.settings" gestion_immobiliere/wsgi.py || {
        echo "Correction de wsgi.py..."
        sed -i 's/DJANGO_SETTINGS_MODULE.*/DJANGO_SETTINGS_MODULE", "gestion_immobiliere.settings")/' gestion_immobiliere/wsgi.py
    }
    
    # Vérifier manage.py
    echo "Vérification de manage.py..."
    grep -q "gestion_immobiliere.settings" manage.py || {
        echo "Correction de manage.py..."
        sed -i 's/DJANGO_SETTINGS_MODULE.*/DJANGO_SETTINGS_MODULE", "gestion_immobiliere.settings")/' manage.py
    }
}

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

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/kbis_immobilier.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "\n${YELLOW}5. CONFIGURATION NGINX${NC}"

# Créer la configuration Nginx correcte
cat > /tmp/kbis_immobilier << 'EOF'
server {
    listen 80;
    server_name localhost 78.138.58.185;

    # Augmenter la limite de taille des requêtes
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    location = /favicon.ico { access_log off; log_not_found off; }

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
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

sudo mv /tmp/kbis_immobilier /etc/nginx/sites-available/
sudo rm -f /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/kbis_immobilier /etc/nginx/sites-enabled/
sudo nginx -t

echo -e "\n${YELLOW}6. COLLECTE DES FICHIERS STATIQUES${NC}"
python3 manage.py collectstatic --noinput

echo -e "\n${YELLOW}7. DÉMARRAGE DES SERVICES${NC}"
sudo systemctl start $SERVICE_NAME
sleep 3
sudo systemctl start nginx

echo -e "\n${YELLOW}8. VÉRIFICATION${NC}"
echo "État des services:"
sudo systemctl status $SERVICE_NAME --no-pager -l
sudo systemctl status nginx --no-pager -l

echo -e "\nTest de connectivité:"
sleep 2
curl -I http://127.0.0.1:8000 2>/dev/null && echo -e "${GREEN}✅ Gunicorn répond sur le port 8000${NC}" || echo -e "${RED}❌ Gunicorn ne répond pas${NC}"
curl -I http://78.138.58.185 2>/dev/null && echo -e "${GREEN}✅ Nginx répond${NC}" || echo -e "${RED}❌ Nginx ne répond pas${NC}"

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Testez maintenant: http://78.138.58.185"




