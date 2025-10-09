#!/bin/bash

# Script maître de déploiement complet - KBIS IMMOBILIER
# Usage: ./master_deploy.sh [clean|deploy|verify]

set -e

echo "🚀 Script Maître de Déploiement KBIS IMMOBILIER"

# Variables
APP_NAME="kbis_immobilier"
APP_DIR="/var/www/$APP_NAME"
REPO_URL="https://github.com/koudougoulaurent/appli_KBIS.git"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_purple() {
    echo -e "${PURPLE}[MASTER]${NC} $1"
}

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  clean    - Nettoyage complet du VPS avec rollback"
    echo "  deploy   - Déploiement complet de l'application"
    echo "  verify   - Vérification de l'état du système"
    echo "  full     - Nettoyage + Déploiement complet"
    echo "  rollback - Restauration depuis la dernière sauvegarde"
    echo "  status   - Statut des services et de l'application"
    echo ""
    echo "Exemples:"
    echo "  $0 clean    # Nettoyer le VPS"
    echo "  $0 deploy   # Déployer l'application"
    echo "  $0 full     # Nettoyage + Déploiement"
    echo "  $0 verify   # Vérifier l'état"
}

# Fonction de nettoyage
clean_vps() {
    log_purple "🧹 PHASE 1: NETTOYAGE COMPLET DU VPS"
    echo "=========================================="
    
    if [ -f "clean_vps_with_rollback.sh" ]; then
        chmod +x clean_vps_with_rollback.sh
        sudo ./clean_vps_with_rollback.sh
    else
        log_error "Script de nettoyage non trouvé: clean_vps_with_rollback.sh"
        exit 1
    fi
    
    log_info "✅ Nettoyage terminé"
}

# Fonction de déploiement
deploy_app() {
    log_purple "🚀 PHASE 2: DÉPLOIEMENT DE L'APPLICATION"
    echo "=========================================="
    
    # Vérification du répertoire
    if [ -d "$APP_DIR" ]; then
        log_warn "Répertoire $APP_DIR existe déjà"
        read -p "Continuer le déploiement? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Déploiement annulé"
            exit 0
        fi
    fi
    
    # Clonage du repository
    log_blue "Clonage du repository..."
    if [ ! -d "$APP_DIR" ]; then
        git clone $REPO_URL $APP_DIR
    else
        cd $APP_DIR
        git pull origin modifications-octobre-2025
    fi
    
    cd $APP_DIR
    
    # Exécution du script de déploiement
    if [ -f "deploy_vps.sh" ]; then
        chmod +x deploy_vps.sh
        sudo ./deploy_vps.sh
    else
        log_error "Script de déploiement non trouvé: deploy_vps.sh"
        exit 1
    fi
    
    log_info "✅ Déploiement terminé"
}

# Fonction de vérification
verify_system() {
    log_purple "🔍 PHASE 3: VÉRIFICATION DU SYSTÈME"
    echo "=========================================="
    
    if [ -f "verify_clean_vps.sh" ]; then
        chmod +x verify_clean_vps.sh
        sudo ./verify_clean_vps.sh
    else
        log_error "Script de vérification non trouvé: verify_clean_vps.sh"
        exit 1
    fi
    
    # Vérification supplémentaire des services
    log_blue "Vérification des services..."
    systemctl is-active kbis_immobilier && log_info "✅ Service Gunicorn actif" || log_error "❌ Service Gunicorn inactif"
    systemctl is-active nginx && log_info "✅ Service Nginx actif" || log_error "❌ Service Nginx inactif"
    
    # Test de connectivité
    log_blue "Test de connectivité..."
    curl -I http://localhost >/dev/null 2>&1 && log_info "✅ HTTP fonctionne" || log_error "❌ HTTP ne fonctionne pas"
    
    log_info "✅ Vérification terminée"
}

# Fonction de rollback
rollback_system() {
    log_purple "🔄 ROLLBACK DU SYSTÈME"
    echo "=========================================="
    
    # Recherche du dernier script de rollback
    LATEST_ROLLBACK=$(ls -t /var/backups/rollback_*.sh 2>/dev/null | head -1)
    
    if [ -z "$LATEST_ROLLBACK" ]; then
        log_error "Aucun script de rollback trouvé"
        exit 1
    fi
    
    log_info "Script de rollback trouvé: $LATEST_ROLLBACK"
    read -p "Exécuter le rollback? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo $LATEST_ROLLBACK
        log_info "✅ Rollback terminé"
    else
        log_info "Rollback annulé"
    fi
}

# Fonction de statut
show_status() {
    log_purple "📊 STATUT DU SYSTÈME"
    echo "=========================================="
    
    # Statut des services
    echo "Services:"
    systemctl status kbis_immobilier --no-pager -l 2>/dev/null || echo "Service Gunicorn non trouvé"
    echo ""
    systemctl status nginx --no-pager -l 2>/dev/null || echo "Service Nginx non trouvé"
    
    # Ports en écoute
    echo ""
    echo "Ports en écoute:"
    netstat -tlnp | grep -E ":(80|443|8000|5432)" || echo "Aucun port important en écoute"
    
    # Espace disque
    echo ""
    echo "Espace disque:"
    df -h | grep -E "(/$|/var)"
    
    # Mémoire
    echo ""
    echo "Mémoire:"
    free -h
}

# Fonction de déploiement complet
full_deploy() {
    log_purple "🎯 DÉPLOIEMENT COMPLET KBIS IMMOBILIER"
    echo "=========================================="
    
    # Phase 1: Nettoyage
    clean_vps
    
    # Phase 2: Déploiement
    deploy_app
    
    # Phase 3: Vérification
    verify_system
    
    log_purple "🎉 DÉPLOIEMENT COMPLET TERMINÉ AVEC SUCCÈS!"
    echo "=========================================="
    log_info "Application disponible sur: http://votre-domaine.com"
    log_info "Logs Gunicorn: journalctl -u kbis_immobilier -f"
    log_info "Logs Nginx: tail -f /var/log/nginx/kbis_immobilier_error.log"
}

# Vérification des privilèges root
if [ "$EUID" -ne 0 ] && [ "$1" != "status" ]; then
    log_error "Ce script doit être exécuté en tant que root (sauf pour 'status')"
    exit 1
fi

# Traitement des arguments
case "${1:-help}" in
    "clean")
        clean_vps
        ;;
    "deploy")
        deploy_app
        ;;
    "verify")
        verify_system
        ;;
    "full")
        full_deploy
        ;;
    "rollback")
        rollback_system
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac
