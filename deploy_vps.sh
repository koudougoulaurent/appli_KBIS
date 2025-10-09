#!/bin/bash

# Script de déploiement pour VPS - KBIS IMMOBILIER
# Usage: ./deploy_vps.sh

set -e

echo "🚀 Déploiement de KBIS IMMOBILIER sur VPS..."

# Variables
APP_NAME="kbis_immobilier"
APP_DIR="/var/www/$APP_NAME"
VENV_DIR="/var/www/$APP_NAME/venv"
SERVICE_NAME="kbis_immobilier"
NGINX_SITE="kbis_immobilier"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des privilèges root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root"
    exit 1
fi

log_info "Mise à jour du système..."
apt update && apt upgrade -y

log_info "Installation des dépendances système..."
apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib nginx redis-server git

log_info "Installation des dépendances Python supplémentaires..."
apt install -y libpq-dev build-essential

log_info "Création du répertoire de l'application..."
mkdir -p $APP_DIR
chown -R www-data:www-data $APP_DIR

log_info "Création de l'environnement virtuel Python..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

log_info "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

log_info "Configuration de PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE kbis_immobilier;"
sudo -u postgres psql -c "CREATE USER kbis_user WITH PASSWORD 'your_password_here';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO kbis_user;"
sudo -u postgres psql -c "ALTER USER kbis_user CREATEDB;"

log_info "Configuration de l'application Django..."
cd $APP_DIR

# Copie des fichiers de configuration
cp env.example .env
log_warn "N'oubliez pas de configurer le fichier .env avec vos paramètres de production"

# Configuration des migrations
python manage.py makemigrations
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Création d'un superutilisateur (optionnel)
log_warn "Création d'un superutilisateur (optionnel)"
python manage.py createsuperuser || true

log_info "Configuration de Gunicorn..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=KBIS IMMOBILIER Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings_production"
ExecStart=$VENV_DIR/bin/gunicorn --config gunicorn.conf.py gestion_immobiliere.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

log_info "Configuration de Nginx..."
cp nginx.conf /etc/nginx/sites-available/$NGINX_SITE
ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test de la configuration Nginx
nginx -t

log_info "Démarrage des services..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl enable nginx
systemctl restart nginx

log_info "Configuration des logs..."
mkdir -p /var/log/gunicorn
mkdir -p /var/log/django
chown -R www-data:www-data /var/log/gunicorn
chown -R www-data:www-data /var/log/django

log_info "Configuration du pare-feu..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

log_info "Déploiement terminé avec succès!"
log_warn "N'oubliez pas de:"
log_warn "1. Configurer le fichier .env avec vos paramètres de production"
log_warn "2. Configurer SSL avec Let's Encrypt si nécessaire"
log_warn "3. Tester l'application sur http://votre-domaine.com"

# Affichage du statut des services
log_info "Statut des services:"
systemctl status $SERVICE_NAME --no-pager
systemctl status nginx --no-pager
