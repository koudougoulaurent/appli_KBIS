#!/bin/bash

# Script de diagnostic pour VPS - KBIS IMMOBILIER
# Usage: ./diagnose_vps.sh

echo "🔍 Diagnostic du VPS KBIS IMMOBILIER..."

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

echo "=========================================="
echo "DIAGNOSTIC COMPLET DU VPS"
echo "=========================================="

# 1. Vérification de l'OS
log_info "1. Système d'exploitation:"
cat /etc/os-release | head -3

# 2. Vérification des services
log_info "2. Statut des services:"
echo "Gunicorn:"
systemctl is-active $SERVICE_NAME 2>/dev/null || log_error "Service Gunicorn non trouvé"
systemctl status $SERVICE_NAME --no-pager -l 2>/dev/null || true

echo ""
echo "Nginx:"
systemctl is-active nginx 2>/dev/null || log_error "Service Nginx non trouvé"
systemctl status nginx --no-pager -l 2>/dev/null || true

# 3. Vérification des ports
log_info "3. Ports en écoute:"
netstat -tlnp | grep -E ":(80|443|8000|5432)" || log_warn "Aucun port important en écoute"

# 4. Vérification de l'application
log_info "4. Structure de l'application:"
if [ -d "$APP_DIR" ]; then
    echo "Répertoire de l'application: $APP_DIR"
    ls -la $APP_DIR | head -10
else
    log_error "Répertoire de l'application non trouvé: $APP_DIR"
fi

# 5. Vérification de l'environnement virtuel
log_info "5. Environnement virtuel:"
if [ -d "$APP_DIR/venv" ]; then
    echo "Environnement virtuel trouvé"
    $APP_DIR/venv/bin/python --version 2>/dev/null || log_error "Python dans venv non fonctionnel"
else
    log_warn "Environnement virtuel non trouvé"
fi

# 6. Vérification de la base de données
log_info "6. Base de données PostgreSQL:"
if command -v psql &> /dev/null; then
    echo "PostgreSQL installé"
    sudo -u postgres psql -c "\l" | grep kbis_immobilier || log_warn "Base de données kbis_immobilier non trouvée"
else
    log_error "PostgreSQL non installé"
fi

# 7. Vérification des logs
log_info "7. Logs récents:"
echo "Logs Gunicorn (dernières 10 lignes):"
journalctl -u $SERVICE_NAME --no-pager -n 10 2>/dev/null || log_warn "Aucun log Gunicorn"

echo ""
echo "Logs Nginx (dernières 10 lignes):"
tail -n 10 /var/log/nginx/error.log 2>/dev/null || log_warn "Aucun log Nginx"

# 8. Vérification de la configuration
log_info "8. Configuration:"
if [ -f "$APP_DIR/.env" ]; then
    echo "Fichier .env trouvé"
    echo "Variables importantes:"
    grep -E "^(DEBUG|SECRET_KEY|DB_|ALLOWED_HOSTS)" $APP_DIR/.env 2>/dev/null || log_warn "Variables importantes manquantes"
else
    log_error "Fichier .env non trouvé"
fi

# 9. Test de connectivité
log_info "9. Test de connectivité:"
echo "Test HTTP local:"
curl -I http://localhost 2>/dev/null && log_info "HTTP fonctionne" || log_error "HTTP ne fonctionne pas"

echo "Test port 8000:"
curl -I http://localhost:8000 2>/dev/null && log_info "Port 8000 fonctionne" || log_warn "Port 8000 ne fonctionne pas"

# 10. Vérification des permissions
log_info "10. Permissions:"
if [ -d "$APP_DIR" ]; then
    echo "Propriétaire de l'application:"
    ls -ld $APP_DIR
    echo "Permissions des fichiers critiques:"
    ls -la $APP_DIR/manage.py 2>/dev/null || log_warn "manage.py non trouvé"
    ls -la $APP_DIR/gunicorn.conf.py 2>/dev/null || log_warn "gunicorn.conf.py non trouvé"
fi

# 11. Vérification de l'espace disque
log_info "11. Espace disque:"
df -h | grep -E "(/$|/var)"

# 12. Vérification de la mémoire
log_info "12. Mémoire:"
free -h

echo "=========================================="
echo "DIAGNOSTIC TERMINÉ"
echo "=========================================="

log_info "Pour réparer l'installation, exécutez:"
echo "  ./fix_vps_deployment.sh"
