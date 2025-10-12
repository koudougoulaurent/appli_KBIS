#!/bin/bash

# Script de déploiement VPS pour KBIS Immobilier
# Configuration PostgreSQL + Nginx + Gunicorn
# Version: 2025-01-27

set -e  # Arrêter en cas d'erreur

echo "🚀 Début du déploiement KBIS Immobilier sur VPS..."

# Variables de configuration
APP_NAME="kbis-immobilier"
APP_USER="kbis"
APP_DIR="/home/$APP_USER/appli_KBIS"
SERVICE_NAME="kbis-immobilier"
NGINX_SITE="kbis-immobilier"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Vérifier si le script est exécuté en tant que root
if [[ $EUID -eq 0 ]]; then
   log_error "Ce script ne doit pas être exécuté en tant que root"
   exit 1
fi

# Mise à jour du système
log_info "Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
log_info "Installation des dépendances système..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    supervisor \
    certbot \
    python3-certbot-nginx

# Configuration de PostgreSQL
log_info "Configuration de PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Création de l'utilisateur et de la base de données
sudo -u postgres psql << EOF
CREATE USER $APP_USER WITH PASSWORD 'kbis_secure_password_2025';
CREATE DATABASE kbis_immobilier OWNER $APP_USER;
GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO $APP_USER;
\q
EOF

# Création du répertoire de l'application
log_info "Création du répertoire de l'application..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Clonage ou mise à jour du code
if [ -d "$APP_DIR/.git" ]; then
    log_info "Mise à jour du code existant..."
    cd $APP_DIR
    git fetch origin
    git checkout modifications-octobre-2025
    git pull origin modifications-octobre-2025
else
    log_info "Clonage du code..."
    git clone -b modifications-octobre-2025 https://github.com/koudougoulaurent/appli_KBIS.git $APP_DIR
    cd $APP_DIR
fi

# Création de l'environnement virtuel
log_info "Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
log_info "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configuration de l'environnement
log_info "Configuration de l'environnement..."
cp .env.production .env

# Édition du fichier .env avec les bonnes valeurs
cat > .env << EOF
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$(curl -s ifconfig.me)
DB_NAME=kbis_immobilier
DB_USER=$APP_USER
DB_PASSWORD=kbis_secure_password_2025
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@$(curl -s ifconfig.me)
SECURE_SSL_REDIRECT=False
EOF

# Création des répertoires nécessaires
log_info "Création des répertoires nécessaires..."
mkdir -p logs
mkdir -p staticfiles
mkdir -p media

# Configuration de Django
log_info "Configuration de Django..."
export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
python manage.py collectstatic --noinput
python manage.py migrate

# Création du superutilisateur (optionnel)
log_info "Création du superutilisateur..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@kbis.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# Configuration de Gunicorn
log_info "Configuration de Gunicorn..."
sudo mkdir -p /var/log/gunicorn
sudo chown $APP_USER:$APP_USER /var/log/gunicorn

# Configuration du service systemd
log_info "Configuration du service systemd..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=KBIS Immobilier Django App
After=network.target postgresql.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production
ExecStart=$APP_DIR/venv/bin/gunicorn --config $APP_DIR/gunicorn.conf.py gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configuration de Nginx
log_info "Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null << EOF
upstream django_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOF

# Activation du site Nginx
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test de la configuration Nginx
sudo nginx -t

# Démarrage des services
log_info "Démarrage des services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl restart nginx

# Vérification du statut des services
log_info "Vérification du statut des services..."
sudo systemctl status $SERVICE_NAME --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status postgresql --no-pager

# Configuration du pare-feu
log_info "Configuration du pare-feu..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Test de l'application
log_info "Test de l'application..."
sleep 5
if curl -f http://localhost > /dev/null 2>&1; then
    log_success "Application déployée avec succès !"
    log_info "URL: http://$(curl -s ifconfig.me)"
    log_info "Admin: http://$(curl -s ifconfig.me)/admin (admin/admin123)"
else
    log_error "Erreur lors du test de l'application"
    log_info "Vérifiez les logs: sudo journalctl -u $SERVICE_NAME -f"
fi

log_success "Déploiement terminé !"
log_info "Pour configurer HTTPS, exécutez: sudo certbot --nginx"
