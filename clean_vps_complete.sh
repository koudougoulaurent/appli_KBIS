#!/bin/bash

# Script de nettoyage complet du VPS
# Supprime l'ancienne installation KBIS et prépare pour un nouveau déploiement

set -e  # Arrêter en cas d'erreur

echo "🧹 Nettoyage complet du VPS - Application KBIS"
echo "=============================================="

# Variables de configuration
APP_NAME="kbis-immobilier"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="kbis-immobilier"
NGINX_SITE="kbis-immobilier"
DB_NAME="kbis_immobilier"
DB_USER="kbis_user"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[ÉTAPE]${NC} $1"
}

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root (utilisez sudo)"
    exit 1
fi

log_step "1. Arrêt des services"
echo "========================"

# Arrêter les services
log_info "Arrêt des services..."
systemctl stop $SERVICE_NAME 2>/dev/null || log_warn "Service $SERVICE_NAME non trouvé"
systemctl stop nginx 2>/dev/null || log_warn "Nginx non trouvé"
systemctl stop mysql 2>/dev/null || log_warn "MySQL non trouvé"

log_step "2. Suppression des services systemd"
echo "====================================="

# Supprimer les services systemd
log_info "Suppression des services systemd..."
rm -f /etc/systemd/system/$SERVICE_NAME.service
rm -f /etc/systemd/system/kbis-*.service
systemctl daemon-reload

log_step "3. Suppression des configurations Nginx"
echo "========================================="

# Supprimer les configurations Nginx
log_info "Suppression des configurations Nginx..."
rm -f /etc/nginx/sites-available/$NGINX_SITE
rm -f /etc/nginx/sites-enabled/$NGINX_SITE
rm -f /etc/nginx/sites-available/kbis-*
rm -f /etc/nginx/sites-enabled/kbis-*

# Restaurer la configuration par défaut de Nginx
if [ ! -f /etc/nginx/sites-enabled/default ]; then
    log_info "Restauration de la configuration Nginx par défaut..."
    cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    
    server_name _;
    
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/
fi

log_step "4. Suppression de l'application"
echo "================================="

# Supprimer l'application
log_info "Suppression du répertoire de l'application..."
rm -rf $APP_DIR
rm -rf /var/www/kbis-*
rm -rf /var/www/appli_KBIS
rm -rf /home/*/appli_KBIS
rm -rf /root/appli_KBIS

log_step "5. Nettoyage de la base de données"
echo "===================================="

# Supprimer la base de données
log_info "Suppression de la base de données..."
systemctl start mysql 2>/dev/null || log_warn "Impossible de démarrer MySQL"

# Essayer de supprimer la base de données
mysql -u root -e "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || log_warn "Impossible de supprimer la base de données"
mysql -u root -e "DROP USER IF EXISTS '$DB_USER'@'localhost';" 2>/dev/null || log_warn "Impossible de supprimer l'utilisateur"

log_step "6. Nettoyage des processus"
echo "============================"

# Tuer tous les processus liés à l'application
log_info "Arrêt des processus Python/Gunicorn..."
pkill -f "gunicorn.*kbis" 2>/dev/null || log_warn "Aucun processus Gunicorn trouvé"
pkill -f "python.*manage.py" 2>/dev/null || log_warn "Aucun processus Python trouvé"
pkill -f "appli_KBIS" 2>/dev/null || log_warn "Aucun processus appli_KBIS trouvé"

log_step "7. Nettoyage des logs"
echo "======================="

# Nettoyer les logs
log_info "Nettoyage des logs..."
rm -rf /var/log/kbis-*
rm -rf /var/log/appli_KBIS*
rm -rf /var/www/*/logs
rm -rf /home/*/logs

# Vider les logs systemd
journalctl --vacuum-time=1d 2>/dev/null || log_warn "Impossible de vider les logs systemd"

log_step "8. Nettoyage des fichiers temporaires"
echo "======================================="

# Nettoyer les fichiers temporaires
log_info "Nettoyage des fichiers temporaires..."
rm -rf /tmp/kbis-*
rm -rf /tmp/appli_KBIS*
rm -rf /tmp/django_*
rm -rf /tmp/gunicorn_*

log_step "9. Nettoyage des caches"
echo "========================="

# Nettoyer les caches
log_info "Nettoyage des caches..."
rm -rf /var/cache/nginx/*
rm -rf /var/cache/apache2/*
rm -rf /tmp/.cache
rm -rf /root/.cache

log_step "10. Nettoyage des packages inutiles"
echo "====================================="

# Supprimer les packages Python inutiles
log_info "Suppression des packages Python inutiles..."
pip3 uninstall -y django gunicorn whitenoise mysqlclient 2>/dev/null || log_warn "Aucun package Python à supprimer"

log_step "11. Nettoyage des fichiers de configuration"
echo "============================================="

# Supprimer les fichiers de configuration
log_info "Suppression des fichiers de configuration..."
rm -f /etc/nginx/conf.d/kbis*
rm -f /etc/nginx/conf.d/appli_KBIS*
rm -f /etc/systemd/system/kbis*
rm -f /etc/systemd/system/appli_KBIS*

log_step "12. Nettoyage des sauvegardes"
echo "==============================="

# Supprimer les sauvegardes
log_info "Suppression des sauvegardes..."
rm -rf /root/backup_kbis*
rm -rf /root/backup_appli_KBIS*
rm -rf /var/backups/kbis*
rm -rf /var/backups/appli_KBIS*

log_step "13. Redémarrage des services essentiels"
echo "========================================="

# Redémarrer les services essentiels
log_info "Redémarrage des services essentiels..."
systemctl restart nginx
systemctl restart mysql

# Vérifier le statut des services
log_info "Vérification du statut des services..."
systemctl status nginx --no-pager
systemctl status mysql --no-pager

log_step "14. Nettoyage final"
echo "====================="

# Nettoyage final
log_info "Nettoyage final..."
apt autoremove -y
apt autoclean
updatedb 2>/dev/null || log_warn "Impossible de mettre à jour la base de données locate"

log_step "15. Vérification du nettoyage"
echo "==============================="

# Vérifier que tout a été supprimé
log_info "Vérification du nettoyage..."

if [ -d "$APP_DIR" ]; then
    log_error "Le répertoire $APP_DIR existe encore"
else
    log_info "✅ Répertoire de l'application supprimé"
fi

if systemctl is-active --quiet $SERVICE_NAME; then
    log_error "Le service $SERVICE_NAME est encore actif"
else
    log_info "✅ Service $SERVICE_NAME arrêté"
fi

if [ -f "/etc/nginx/sites-enabled/$NGINX_SITE" ]; then
    log_error "La configuration Nginx $NGINX_SITE existe encore"
else
    log_info "✅ Configuration Nginx supprimée"
fi

# Vérifier les processus
if pgrep -f "gunicorn.*kbis" > /dev/null; then
    log_error "Des processus Gunicorn sont encore actifs"
else
    log_info "✅ Aucun processus Gunicorn actif"
fi

log_info "🎉 Nettoyage terminé avec succès!"
echo ""
echo "📋 Résumé du nettoyage:"
echo "======================="
echo "✅ Services arrêtés et supprimés"
echo "✅ Configuration Nginx nettoyée"
echo "✅ Application supprimée"
echo "✅ Base de données nettoyée"
echo "✅ Logs et caches vidés"
echo "✅ Processus terminés"
echo "✅ Fichiers temporaires supprimés"
echo ""
echo "🚀 Le VPS est maintenant propre et prêt pour un nouveau déploiement!"
echo ""
echo "📝 Prochaines étapes:"
echo "1. Exécuter le script de déploiement propre"
echo "2. Vérifier que tout fonctionne correctement"
echo "3. Configurer HTTPS si nécessaire"
echo ""
echo "💡 Pour déployer la nouvelle version:"
echo "   wget https://raw.githubusercontent.com/koudougoulaurent/appli_KBIS/modifications-octobre-2025/deploy_vps_clean.sh"
echo "   chmod +x deploy_vps_clean.sh"
echo "   ./deploy_vps_clean.sh"
