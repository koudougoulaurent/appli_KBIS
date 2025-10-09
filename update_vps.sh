#!/bin/bash

# Script de mise à jour pour VPS existant - KBIS IMMOBILIER
# Usage: ./update_vps.sh

set -e

echo "🔄 Mise à jour du VPS existant..."

# Variables
APP_NAME="kbis_immobilier"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="kbis_immobilier"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

log_info "Arrêt des services..."
systemctl stop $SERVICE_NAME 2>/dev/null || true

log_info "Sauvegarde de la configuration actuelle..."
BACKUP_DIR="/var/backups/kbis_immobilier_update_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
if [ -d "$APP_DIR" ]; then
    cp -r $APP_DIR $BACKUP_DIR/
    log_info "Sauvegarde créée dans $BACKUP_DIR"
fi

log_info "Mise à jour du code source..."
cd $APP_DIR
git fetch origin
git reset --hard origin/modifications-octobre-2025

log_info "Mise à jour de l'environnement virtuel..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    log_error "Environnement virtuel non trouvé"
    exit 1
fi

log_info "Application des migrations..."
python manage.py makemigrations
python manage.py migrate

log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

log_info "Redémarrage des services..."
systemctl daemon-reload
systemctl start $SERVICE_NAME
systemctl restart nginx

log_info "Vérification du statut..."
sleep 5
systemctl status $SERVICE_NAME --no-pager

log_info "Mise à jour terminée avec succès!"
log_warn "L'ancienne version est sauvegardée dans $BACKUP_DIR"
