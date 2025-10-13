#!/bin/bash

# ===========================================
# SYSTÈME DE ROLLBACK KBIS IMMOBILIER
# ===========================================
# Ce script permet de revenir rapidement à une version précédente
# Usage: ./rollback_system.sh [backup_name] [options]

set -e

# Configuration
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"
SERVICE_NAME="kbis-immobilier"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Vérifier qu'une sauvegarde existe
check_backup_exists() {
    local backup_name=$1
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [ ! -d "$backup_path" ]; then
        log_error "Sauvegarde non trouvée: $backup_name"
        log "Sauvegardes disponibles:"
        ls -1 "$BACKUP_DIR" | grep -E "^(full|data|config|quick)_" | head -10
        exit 1
    fi
    
    echo "$backup_path"
}

# Arrêter les services
stop_services() {
    log "🛑 Arrêt des services..."
    
    # Arrêter le service Django
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        log_success "Service $SERVICE_NAME arrêté"
    else
        log_warning "Service $SERVICE_NAME déjà arrêté"
    fi
    
    # Arrêter Nginx si nécessaire
    if systemctl is-active --quiet nginx; then
        systemctl stop nginx
        log_success "Nginx arrêté"
    fi
}

# Démarrer les services
start_services() {
    log "🚀 Démarrage des services..."
    
    # Démarrer le service Django
    systemctl start "$SERVICE_NAME"
    sleep 3
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Service $SERVICE_NAME démarré"
    else
        log_error "Échec du démarrage du service $SERVICE_NAME"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
    
    # Démarrer Nginx
    systemctl start nginx
    if systemctl is-active --quiet nginx; then
        log_success "Nginx démarré"
    else
        log_error "Échec du démarrage de Nginx"
        exit 1
    fi
}

# Rollback complet
rollback_full() {
    local backup_path=$1
    local dry_run=$2
    
    log "🔄 Rollback complet depuis: $backup_path"
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune modification ne sera effectuée"
        return 0
    fi
    
    # Arrêter les services
    stop_services
    
    # Créer une sauvegarde de sécurité avant rollback
    log "💾 Création d'une sauvegarde de sécurité..."
    ./backup_system.sh quick
    
    # Restaurer la base de données
    if [ -f "$backup_path/db.sqlite3" ]; then
        log "📊 Restauration de la base de données..."
        cp "$backup_path/db.sqlite3" "$APP_DIR/"
        chown kbis:kbis "$APP_DIR/db.sqlite3"
        chmod 664 "$APP_DIR/db.sqlite3"
        log_success "Base de données restaurée"
    fi
    
    # Restaurer les fichiers média
    if [ -d "$backup_path/media" ]; then
        log "📁 Restauration des fichiers média..."
        rm -rf "$APP_DIR/media"
        cp -r "$backup_path/media" "$APP_DIR/"
        chown -R kbis:kbis "$APP_DIR/media"
        log_success "Fichiers média restaurés"
    fi
    
    # Restaurer les fichiers statiques
    if [ -d "$backup_path/staticfiles" ]; then
        log "🎨 Restauration des fichiers statiques..."
        rm -rf "$APP_DIR/staticfiles"
        cp -r "$backup_path/staticfiles" "$APP_DIR/"
        chown -R kbis:kbis "$APP_DIR/staticfiles"
        log_success "Fichiers statiques restaurés"
    fi
    
    # Restaurer les configurations
    if [ -d "$backup_path/config" ]; then
        log "⚙️  Restauration des configurations..."
        for config_file in "$backup_path/config"/*; do
            if [ -f "$config_file" ]; then
                local filename=$(basename "$config_file")
                case "$filename" in
                    "kbis-immobilier")
                        cp "$config_file" "/etc/nginx/sites-available/"
                        nginx -t && systemctl reload nginx
                        log "  ✓ Configuration Nginx restaurée"
                        ;;
                    "kbis-immobilier.service")
                        cp "$config_file" "/etc/systemd/system/"
                        systemctl daemon-reload
                        log "  ✓ Configuration systemd restaurée"
                        ;;
                    ".env")
                        cp "$config_file" "$APP_DIR/"
                        chown kbis:kbis "$APP_DIR/.env"
                        log "  ✓ Configuration .env restaurée"
                        ;;
                    "gunicorn.conf.py")
                        cp "$config_file" "$APP_DIR/"
                        chown kbis:kbis "$APP_DIR/gunicorn.conf.py"
                        log "  ✓ Configuration Gunicorn restaurée"
                        ;;
                esac
            fi
        done
    fi
    
    # Restaurer le code source
    if [ -d "$backup_path/code" ]; then
        log "💻 Restauration du code source..."
        # Sauvegarder le venv actuel
        if [ -d "$APP_DIR/venv" ]; then
            mv "$APP_DIR/venv" "$APP_DIR/venv_backup_$(date +%s)"
        fi
        
        # Restaurer le code
        rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
              --exclude='db.sqlite3' --exclude='media' --exclude='staticfiles' \
              "$backup_path/code/" "$APP_DIR/"
        
        # Restaurer le venv si disponible
        if [ -d "$APP_DIR/venv_backup_"* ]; then
            mv "$APP_DIR/venv_backup_"* "$APP_DIR/venv"
        fi
        
        chown -R kbis:kbis "$APP_DIR"
        log_success "Code source restauré"
    fi
    
    # Démarrer les services
    start_services
    
    log_success "Rollback complet terminé"
}

# Rollback des données uniquement
rollback_data() {
    local backup_path=$1
    local dry_run=$2
    
    log "🔄 Rollback des données depuis: $backup_path"
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune modification ne sera effectuée"
        return 0
    fi
    
    # Arrêter les services
    stop_services
    
    # Créer une sauvegarde de sécurité
    log "💾 Création d'une sauvegarde de sécurité..."
    ./backup_system.sh quick
    
    # Restaurer la base de données
    if [ -f "$backup_path/db.sqlite3" ]; then
        log "📊 Restauration de la base de données..."
        cp "$backup_path/db.sqlite3" "$APP_DIR/"
        chown kbis:kbis "$APP_DIR/db.sqlite3"
        chmod 664 "$APP_DIR/db.sqlite3"
        log_success "Base de données restaurée"
    fi
    
    # Restaurer les fichiers média
    if [ -d "$backup_path/media" ]; then
        log "📁 Restauration des fichiers média..."
        rm -rf "$APP_DIR/media"
        cp -r "$backup_path/media" "$APP_DIR/"
        chown -R kbis:kbis "$APP_DIR/media"
        log_success "Fichiers média restaurés"
    fi
    
    # Démarrer les services
    start_services
    
    log_success "Rollback des données terminé"
}

# Rollback de configuration
rollback_config() {
    local backup_path=$1
    local dry_run=$2
    
    log "🔄 Rollback des configurations depuis: $backup_path"
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune modification ne sera effectuée"
        return 0
    fi
    
    # Arrêter les services
    stop_services
    
    # Restaurer les configurations
    log "⚙️  Restauration des configurations..."
    for config_file in "$backup_path"/*; do
        if [ -f "$config_file" ]; then
            local filename=$(basename "$config_file")
            case "$filename" in
                "kbis-immobilier")
                    cp "$config_file" "/etc/nginx/sites-available/"
                    nginx -t && systemctl reload nginx
                    log "  ✓ Configuration Nginx restaurée"
                    ;;
                "kbis-immobilier.service")
                    cp "$config_file" "/etc/systemd/system/"
                    systemctl daemon-reload
                    log "  ✓ Configuration systemd restaurée"
                    ;;
                ".env")
                    cp "$config_file" "$APP_DIR/"
                    chown kbis:kbis "$APP_DIR/.env"
                    log "  ✓ Configuration .env restaurée"
                    ;;
                "gunicorn.conf.py")
                    cp "$config_file" "$APP_DIR/"
                    chown kbis:kbis "$APP_DIR/gunicorn.conf.py"
                    log "  ✓ Configuration Gunicorn restaurée"
                    ;;
            esac
        fi
    done
    
    # Démarrer les services
    start_services
    
    log_success "Rollback des configurations terminé"
}

# Vérifier la santé du service après rollback
health_check() {
    log "🏥 Vérification de la santé du service..."
    
    # Attendre que le service soit prêt
    sleep 5
    
    # Vérifier le statut du service
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_error "Le service $SERVICE_NAME n'est pas actif"
        return 1
    fi
    
    # Vérifier la réponse HTTP
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
            log_success "Service accessible via HTTP"
            break
        else
            log "Tentative $attempt/$max_attempts - Attente..."
            sleep 2
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Le service n'est pas accessible après $max_attempts tentatives"
        return 1
    fi
    
    # Vérifier la base de données
    if [ -f "$APP_DIR/db.sqlite3" ]; then
        if sqlite3 "$APP_DIR/db.sqlite3" "SELECT 1;" > /dev/null 2>&1; then
            log_success "Base de données accessible"
        else
            log_error "Problème avec la base de données"
            return 1
        fi
    fi
    
    log_success "Vérification de santé terminée - Service opérationnel"
}

# Lister les sauvegardes disponibles
list_backups() {
    log "📋 Sauvegardes disponibles pour rollback:"
    echo
    for backup_type in full data config quick; do
        echo "=== $backup_type ==="
        ls -1t "$BACKUP_DIR" | grep "^${backup_type}_" | head -5 | while read -r backup; do
            local info_file="$BACKUP_DIR/$backup/backup_info.txt"
            if [ -f "$info_file" ]; then
                echo "  📁 $backup ($(grep "Taille:" "$info_file" | cut -d' ' -f2))"
                echo "     $(grep "Date:" "$info_file" | cut -d' ' -f2-)"
            else
                echo "  📁 $backup"
            fi
        done
        echo
    done
}

# Fonction principale
main() {
    local backup_name=$1
    local dry_run=${2:-"false"}
    
    # Vérifier les arguments
    if [ -z "$backup_name" ]; then
        echo "Usage: $0 <backup_name> [--dry-run]"
        echo
        echo "Options:"
        echo "  --dry-run    Mode simulation (aucune modification)"
        echo
        echo "Sauvegardes disponibles:"
        list_backups
        exit 1
    fi
    
    # Vérifier si c'est un dry-run
    if [ "$2" = "--dry-run" ]; then
        dry_run="true"
    fi
    
    # Vérifier que la sauvegarde existe
    local backup_path=$(check_backup_exists "$backup_name")
    
    # Déterminer le type de rollback
    local backup_type=$(echo "$backup_name" | cut -d'_' -f1)
    
    case "$backup_type" in
        "full")
            rollback_full "$backup_path" "$dry_run"
            ;;
        "data")
            rollback_data "$backup_path" "$dry_run"
            ;;
        "config")
            rollback_config "$backup_path" "$dry_run"
            ;;
        "quick")
            rollback_data "$backup_path" "$dry_run"
            ;;
        *)
            log_error "Type de sauvegarde non reconnu: $backup_type"
            exit 1
            ;;
    esac
    
    # Vérification de santé (sauf en mode dry-run)
    if [ "$dry_run" = "false" ]; then
        health_check
    fi
    
    log_success "Rollback terminé avec succès!"
}

# Exécution
main "$@"
