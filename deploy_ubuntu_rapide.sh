#!/bin/bash

# Script de déploiement rapide pour VPS Ubuntu
# Dépôt: https://github.com/koudougoulaurent/appli_KBIS.git
# Branche: modifications-octobre-2025

set -e

# Variables
VPS_IP=""
DOMAIN=""
APP_USER="kbis"
APP_DIR="/home/$APP_USER/appli_KBIS"
REPO_URL="https://github.com/koudougoulaurent/appli_KBIS.git"
BRANCH="modifications-octobre-2025"

# Couleurs
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

# Demander les informations
if [ -z "$VPS_IP" ]; then
    read -p "Entrez l'IP de votre VPS Ubuntu: " VPS_IP
fi

if [ -z "$DOMAIN" ]; then
    read -p "Entrez votre domaine (optionnel, laissez vide si pas de domaine): " DOMAIN
fi

log_info "Déploiement sur VPS Ubuntu: $VPS_IP"
if [ ! -z "$DOMAIN" ]; then
    log_info "Domaine: $DOMAIN"
fi

# Création du script de déploiement complet
cat > deploy_ubuntu_complete.sh << 'EOF'
#!/bin/bash

# Script de déploiement complet pour Ubuntu
set -e

# Variables
APP_NAME="kbis-immobilier"
APP_USER="kbis"
APP_DIR="/home/$APP_USER/appli_KBIS"
SERVICE_NAME="kbis-immobilier"
NGINX_SITE="kbis-immobilier"
REPO_URL="https://github.com/koudougoulaurent/appli_KBIS.git"
BRANCH="modifications-octobre-2025"

# Couleurs
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

# Mise à jour du système
log_info "Mise à jour du système Ubuntu..."
apt update && apt upgrade -y

# Installation des dépendances
log_info "Installation des dépendances..."
apt install -y \
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

# Configuration PostgreSQL
log_info "Configuration PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Création de l'utilisateur et base de données
sudo -u postgres psql << PSQL_EOF
CREATE USER $APP_USER WITH PASSWORD 'kbis_secure_password_2025';
CREATE DATABASE kbis_immobilier OWNER $APP_USER;
GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO $APP_USER;
\q
PSQL_EOF

# Création de l'utilisateur système
log_info "Création de l'utilisateur application..."
adduser --disabled-password --gecos "" $APP_USER
usermod -aG sudo $APP_USER

# Création du répertoire
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# Clonage du code
log_info "Clonage du code depuis GitHub..."
cd /tmp
git clone -b $BRANCH $REPO_URL
cp -r appli_KBIS/* $APP_DIR/
chown -R $APP_USER:$APP_USER $APP_DIR

# Configuration de l'application
log_info "Configuration de l'application..."
cd $APP_DIR
su - $APP_USER -c "cd $APP_DIR && python3 -m venv venv"
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Configuration de l'environnement
log_info "Configuration de l'environnement..."
cat > $APP_DIR/.env << ENV_EOF
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')
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
DEFAULT_FROM_EMAIL=noreply@$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')
SECURE_SSL_REDIRECT=False
ENV_EOF

# Création des répertoires
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/staticfiles
mkdir -p $APP_DIR/media
chown -R $APP_USER:$APP_USER $APP_DIR

# Configuration Django
log_info "Configuration Django..."
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production && python manage.py collectstatic --noinput"
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production && python manage.py migrate"

# Création du superutilisateur
log_info "Création du superutilisateur..."
su - $APP_USER -c "cd $APP_DIR && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production && echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@kbis.com', 'admin123') if not User.objects.filter(username='admin').exists() else None\" | python manage.py shell"

# Configuration Gunicorn
mkdir -p /var/log/gunicorn
chown $APP_USER:$APP_USER /var/log/gunicorn

# Configuration du service systemd
log_info "Configuration du service systemd..."
cat > /etc/systemd/system/$SERVICE_NAME.service << SERVICE_EOF
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
SERVICE_EOF

# Configuration Nginx
log_info "Configuration Nginx..."
cat > /etc/nginx/sites-available/$NGINX_SITE << NGINX_EOF
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
NGINX_EOF

# Activation du site Nginx
ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test de la configuration Nginx
nginx -t

# Démarrage des services
log_info "Démarrage des services..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl restart nginx

# Configuration du pare-feu
log_info "Configuration du pare-feu..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Test de l'application
log_info "Test de l'application..."
sleep 5
if curl -f http://localhost > /dev/null 2>&1; then
    log_success "Application déployée avec succès !"
    log_info "URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')"
    log_info "Admin: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')/admin (admin/admin123)"
else
    log_error "Erreur lors du test de l'application"
    log_info "Vérifiez les logs: journalctl -u $SERVICE_NAME -f"
fi

log_success "Déploiement terminé !"
EOF

# Envoi et exécution du script
log_info "Envoi du script vers le VPS..."
scp deploy_ubuntu_complete.sh root@$VPS_IP:/tmp/

log_info "Exécution du déploiement sur le VPS..."
ssh root@$VPS_IP "chmod +x /tmp/deploy_ubuntu_complete.sh && /tmp/deploy_ubuntu_complete.sh"

# Nettoyage
rm -f deploy_ubuntu_complete.sh

log_success "Déploiement terminé !"
log_info "URL de l'application: http://$VPS_IP"
log_info "Admin: http://$VPS_IP/admin (admin/admin123)"

if [ ! -z "$DOMAIN" ]; then
    log_info "Pour configurer HTTPS avec le domaine $DOMAIN:"
    log_info "  ssh root@$VPS_IP"
    log_info "  certbot --nginx -d $DOMAIN"
fi
