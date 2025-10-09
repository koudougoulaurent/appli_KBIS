#!/bin/bash

# Script de réparation pour VPS existant - KBIS IMMOBILIER
# Usage: ./fix_vps_deployment.sh

set -e

echo "🔧 Réparation du déploiement VPS existant..."

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

log_info "Arrêt des services existants..."
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

log_info "Sauvegarde de l'ancienne version..."
BACKUP_DIR="/var/backups/kbis_immobilier_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
if [ -d "$APP_DIR" ]; then
    cp -r $APP_DIR $BACKUP_DIR/
    log_info "Sauvegarde créée dans $BACKUP_DIR"
fi

log_info "Nettoyage de l'ancienne installation..."
rm -rf $APP_DIR
mkdir -p $APP_DIR

log_info "Clonage de la nouvelle version..."
cd /var/www
git clone <VOTRE_REPO_URL> $APP_NAME
cd $APP_NAME

log_info "Création de l'environnement virtuel..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

log_info "Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

log_info "Configuration de l'environnement..."
if [ ! -f .env ]; then
    cp env.example .env
    log_warn "Fichier .env créé depuis env.example - CONFIGUREZ-LE !"
fi

log_info "Configuration de la base de données..."
# Vérification si PostgreSQL est installé
if ! command -v psql &> /dev/null; then
    log_info "Installation de PostgreSQL..."
    apt update
    apt install -y postgresql postgresql-contrib
fi

# Configuration de la base de données
sudo -u postgres psql -c "DROP DATABASE IF EXISTS kbis_immobilier;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE kbis_immobilier;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER kbis_user WITH PASSWORD 'kbis_password_2024';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kbis_immobilier TO kbis_user;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER kbis_user CREATEDB;" 2>/dev/null || true

log_info "Application des migrations..."
python manage.py makemigrations
python manage.py migrate

log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

log_info "Création d'un superutilisateur..."
log_warn "Création d'un superutilisateur (optionnel)"
python manage.py createsuperuser || true

log_info "Configuration des permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

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

log_info "Configuration des logs..."
mkdir -p /var/log/gunicorn
mkdir -p /var/log/django
chown -R www-data:www-data /var/log/gunicorn
chown -R www-data:www-data /var/log/django

log_info "Démarrage des services..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl enable nginx
systemctl restart nginx

log_info "Vérification du statut des services..."
sleep 5
systemctl status $SERVICE_NAME --no-pager
systemctl status nginx --no-pager

log_info "Test de l'application..."
curl -I http://localhost || log_warn "Test HTTP échoué - vérifiez la configuration"

log_info "Réparation terminée avec succès!"
log_warn "IMPORTANT:"
log_warn "1. Configurez le fichier .env avec vos paramètres de production"
log_warn "2. Vérifiez la configuration de la base de données"
log_warn "3. Testez l'application sur http://votre-domaine.com"
log_warn "4. L'ancienne version est sauvegardée dans $BACKUP_DIR"

echo ""
log_info "Commandes utiles:"
echo "  - Logs Gunicorn: journalctl -u $SERVICE_NAME -f"
echo "  - Logs Nginx: tail -f /var/log/nginx/kbis_immobilier_error.log"
echo "  - Redémarrage: systemctl restart $SERVICE_NAME"
echo "  - Test: curl http://localhost"
