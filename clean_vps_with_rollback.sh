#!/bin/bash

# Script de nettoyage complet VPS avec rollback - KBIS IMMOBILIER
# Usage: ./clean_vps_with_rollback.sh

set -e

echo "🧹 Nettoyage complet du VPS avec possibilité de rollback..."

# Variables
APP_NAME="kbis_immobilier"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="kbis_immobilier"
NGINX_SITE="kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier_cleanup_$(date +%Y%m%d_%H%M%S)"
ROLLBACK_SCRIPT="/var/backups/rollback_$(date +%Y%m%d_%H%M%S).sh"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_blue() {
    echo -e "${BLUE}[BACKUP]${NC} $1"
}

# Vérification des privilèges root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root"
    exit 1
fi

echo "=========================================="
echo "NETTOYAGE COMPLET VPS AVEC ROLLBACK"
echo "=========================================="

# 1. Création du répertoire de sauvegarde
log_blue "1. Création du répertoire de sauvegarde..."
mkdir -p $BACKUP_DIR
log_info "Sauvegarde dans: $BACKUP_DIR"

# 2. Sauvegarde de l'application existante
log_blue "2. Sauvegarde de l'application existante..."
if [ -d "$APP_DIR" ]; then
    cp -r $APP_DIR $BACKUP_DIR/application_backup
    log_info "Application sauvegardée"
else
    log_warn "Aucune application existante trouvée"
fi

# 3. Sauvegarde de la configuration Nginx
log_blue "3. Sauvegarde de la configuration Nginx..."
if [ -f "/etc/nginx/sites-available/$NGINX_SITE" ]; then
    cp /etc/nginx/sites-available/$NGINX_SITE $BACKUP_DIR/nginx_site.conf
    log_info "Configuration Nginx sauvegardée"
fi

if [ -L "/etc/nginx/sites-enabled/$NGINX_SITE" ]; then
    echo "Lien symbolique Nginx existant" > $BACKUP_DIR/nginx_symlink.txt
    log_info "Lien symbolique Nginx documenté"
fi

# 4. Sauvegarde de la configuration systemd
log_blue "4. Sauvegarde de la configuration systemd..."
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    cp /etc/systemd/system/$SERVICE_NAME.service $BACKUP_DIR/systemd_service.service
    log_info "Service systemd sauvegardé"
fi

# 5. Sauvegarde de la base de données
log_blue "5. Sauvegarde de la base de données..."
if command -v psql &> /dev/null; then
    sudo -u postgres pg_dump kbis_immobilier > $BACKUP_DIR/database_backup.sql 2>/dev/null || log_warn "Impossible de sauvegarder la base de données"
    log_info "Base de données sauvegardée"
fi

# 6. Sauvegarde des logs
log_blue "6. Sauvegarde des logs..."
mkdir -p $BACKUP_DIR/logs
if [ -d "/var/log/gunicorn" ]; then
    cp -r /var/log/gunicorn $BACKUP_DIR/logs/ 2>/dev/null || true
fi
if [ -d "/var/log/django" ]; then
    cp -r /var/log/django $BACKUP_DIR/logs/ 2>/dev/null || true
fi
journalctl -u $SERVICE_NAME --no-pager > $BACKUP_DIR/logs/gunicorn_journal.log 2>/dev/null || true
log_info "Logs sauvegardés"

# 7. Création du script de rollback
log_blue "7. Création du script de rollback..."
cat > $ROLLBACK_SCRIPT << EOF
#!/bin/bash
# Script de rollback automatique - KBIS IMMOBILIER
# Créé le: $(date)

echo "🔄 Restauration depuis la sauvegarde..."

# Arrêt des services
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# Restauration de l'application
if [ -d "$BACKUP_DIR/application_backup" ]; then
    rm -rf $APP_DIR
    cp -r $BACKUP_DIR/application_backup $APP_DIR
    chown -R www-data:www-data $APP_DIR
    echo "✅ Application restaurée"
fi

# Restauration de la configuration Nginx
if [ -f "$BACKUP_DIR/nginx_site.conf" ]; then
    cp $BACKUP_DIR/nginx_site.conf /etc/nginx/sites-available/$NGINX_SITE
    ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
    echo "✅ Configuration Nginx restaurée"
fi

# Restauration du service systemd
if [ -f "$BACKUP_DIR/systemd_service.service" ]; then
    cp $BACKUP_DIR/systemd_service.service /etc/systemd/system/$SERVICE_NAME.service
    systemctl daemon-reload
    echo "✅ Service systemd restauré"
fi

# Restauration de la base de données
if [ -f "$BACKUP_DIR/database_backup.sql" ]; then
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS kbis_immobilier;"
    sudo -u postgres psql -c "CREATE DATABASE kbis_immobilier;"
    sudo -u postgres psql kbis_immobilier < $BACKUP_DIR/database_backup.sql
    echo "✅ Base de données restaurée"
fi

# Redémarrage des services
systemctl start $SERVICE_NAME
systemctl restart nginx

echo "✅ Rollback terminé avec succès!"
echo "📁 Sauvegarde conservée dans: $BACKUP_DIR"
EOF

chmod +x $ROLLBACK_SCRIPT
log_info "Script de rollback créé: $ROLLBACK_SCRIPT"

# 8. Nettoyage complet
log_blue "8. Nettoyage complet du système..."

# Arrêt des services
log_info "Arrêt des services..."
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# Suppression de l'application
log_info "Suppression de l'application..."
rm -rf $APP_DIR

# Suppression du service systemd
log_info "Suppression du service systemd..."
systemctl disable $SERVICE_NAME 2>/dev/null || true
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload

# Suppression de la configuration Nginx
log_info "Suppression de la configuration Nginx..."
rm -f /etc/nginx/sites-available/$NGINX_SITE
rm -f /etc/nginx/sites-enabled/$NGINX_SITE
rm -f /etc/nginx/sites-enabled/default

# Suppression des logs
log_info "Suppression des logs..."
rm -rf /var/log/gunicorn
rm -rf /var/log/django

# Suppression de la base de données (optionnel)
read -p "Voulez-vous supprimer la base de données PostgreSQL? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Suppression de la base de données..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS kbis_immobilier;" 2>/dev/null || true
    sudo -u postgres psql -c "DROP USER IF EXISTS kbis_user;" 2>/dev/null || true
fi

# Nettoyage des packages (optionnel)
read -p "Voulez-vous supprimer les packages Python et PostgreSQL? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Suppression des packages..."
    apt remove --purge -y python3-pip python3-venv postgresql postgresql-contrib nginx redis-server 2>/dev/null || true
    apt autoremove -y
fi

# 9. Vérification du nettoyage
log_blue "9. Vérification du nettoyage..."
echo "Vérification des répertoires:"
ls -la /var/www/ | grep $APP_NAME || log_info "✅ Répertoire application supprimé"

echo "Vérification des services:"
systemctl list-units --type=service | grep $SERVICE_NAME || log_info "✅ Service supprimé"

echo "Vérification Nginx:"
ls -la /etc/nginx/sites-enabled/ | grep $NGINX_SITE || log_info "✅ Configuration Nginx supprimée"

# 10. Résumé final
echo "=========================================="
echo "NETTOYAGE TERMINÉ AVEC SUCCÈS"
echo "=========================================="

log_info "✅ VPS nettoyé complètement"
log_info "📁 Sauvegarde complète dans: $BACKUP_DIR"
log_info "🔄 Script de rollback: $ROLLBACK_SCRIPT"

echo ""
log_warn "COMMANDES UTILES:"
echo "  - Rollback complet: sudo $ROLLBACK_SCRIPT"
echo "  - Voir la sauvegarde: ls -la $BACKUP_DIR"
echo "  - Redéployer: git clone <repo> $APP_DIR && sudo ./deploy_vps.sh"

echo ""
log_info "Le VPS est maintenant propre et prêt pour un nouveau déploiement!"
