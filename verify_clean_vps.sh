#!/bin/bash

# Script de vérification post-nettoyage VPS - KBIS IMMOBILIER
# Usage: ./verify_clean_vps.sh

echo "🔍 Vérification du nettoyage VPS..."

# Variables
APP_NAME="kbis_immobilier"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="kbis_immobilier"
NGINX_SITE="kbis_immobilier"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "VÉRIFICATION POST-NETTOYAGE VPS"
echo "=========================================="

# 1. Vérification des répertoires
echo "1. Vérification des répertoires:"
if [ -d "$APP_DIR" ]; then
    log_error "Répertoire application encore présent: $APP_DIR"
else
    log_info "Répertoire application supprimé"
fi

# 2. Vérification des services
echo "2. Vérification des services:"
if systemctl is-active $SERVICE_NAME &>/dev/null; then
    log_error "Service $SERVICE_NAME encore actif"
else
    log_info "Service $SERVICE_NAME arrêté"
fi

if systemctl is-enabled $SERVICE_NAME &>/dev/null; then
    log_error "Service $SERVICE_NAME encore activé"
else
    log_info "Service $SERVICE_NAME désactivé"
fi

# 3. Vérification des fichiers de configuration
echo "3. Vérification des fichiers de configuration:"
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    log_error "Fichier service systemd encore présent"
else
    log_info "Fichier service systemd supprimé"
fi

if [ -f "/etc/nginx/sites-available/$NGINX_SITE" ]; then
    log_error "Configuration Nginx encore présente"
else
    log_info "Configuration Nginx supprimée"
fi

if [ -L "/etc/nginx/sites-enabled/$NGINX_SITE" ]; then
    log_error "Lien symbolique Nginx encore présent"
else
    log_info "Lien symbolique Nginx supprimé"
fi

# 4. Vérification des logs
echo "4. Vérification des logs:"
if [ -d "/var/log/gunicorn" ]; then
    log_warn "Répertoire logs Gunicorn encore présent"
else
    log_info "Logs Gunicorn supprimés"
fi

if [ -d "/var/log/django" ]; then
    log_warn "Répertoire logs Django encore présent"
else
    log_info "Logs Django supprimés"
fi

# 5. Vérification des ports
echo "5. Vérification des ports:"
if netstat -tlnp | grep -q ":8000"; then
    log_error "Port 8000 encore en écoute"
else
    log_info "Port 8000 libre"
fi

if netstat -tlnp | grep -q ":80"; then
    log_warn "Port 80 en écoute (Nginx peut être actif)"
else
    log_info "Port 80 libre"
fi

# 6. Vérification de la base de données
echo "6. Vérification de la base de données:"
if command -v psql &> /dev/null; then
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw kbis_immobilier; then
        log_warn "Base de données kbis_immobilier encore présente"
    else
        log_info "Base de données kbis_immobilier supprimée"
    fi
else
    log_info "PostgreSQL non installé"
fi

# 7. Vérification des processus
echo "7. Vérification des processus:"
if pgrep -f "gunicorn.*kbis" > /dev/null; then
    log_error "Processus Gunicorn KBIS encore en cours"
else
    log_info "Processus Gunicorn KBIS arrêtés"
fi

if pgrep -f "python.*manage.py" > /dev/null; then
    log_warn "Processus Django encore en cours"
else
    log_info "Processus Django arrêtés"
fi

# 8. Vérification de l'espace disque
echo "8. Vérification de l'espace disque:"
df -h | grep -E "(/$|/var)" | while read line; do
    echo "  $line"
done

# 9. Vérification de la mémoire
echo "9. Vérification de la mémoire:"
free -h

# 10. Résumé
echo "=========================================="
echo "RÉSUMÉ DE LA VÉRIFICATION"
echo "=========================================="

# Compter les erreurs
ERRORS=0
WARNINGS=0

# Vérifications simples
[ -d "$APP_DIR" ] && ((ERRORS++))
systemctl is-active $SERVICE_NAME &>/dev/null && ((ERRORS++))
systemctl is-enabled $SERVICE_NAME &>/dev/null && ((ERRORS++))
[ -f "/etc/systemd/system/$SERVICE_NAME.service" ] && ((ERRORS++))
[ -f "/etc/nginx/sites-available/$NGINX_SITE" ] && ((ERRORS++))
[ -L "/etc/nginx/sites-enabled/$NGINX_SITE" ] && ((ERRORS++))
netstat -tlnp | grep -q ":8000" && ((ERRORS++))
pgrep -f "gunicorn.*kbis" > /dev/null && ((ERRORS++))

[ -d "/var/log/gunicorn" ] && ((WARNINGS++))
[ -d "/var/log/django" ] && ((WARNINGS++))

if [ $ERRORS -eq 0 ]; then
    log_info "✅ Nettoyage parfait - Aucune erreur détectée"
    if [ $WARNINGS -eq 0 ]; then
        log_info "✅ Nettoyage complet - Aucun avertissement"
    else
        log_warn "⚠️  $WARNINGS avertissement(s) - Nettoyage partiel"
    fi
else
    log_error "❌ $ERRORS erreur(s) détectée(s) - Nettoyage incomplet"
fi

echo ""
log_info "Le VPS est prêt pour un nouveau déploiement!"
