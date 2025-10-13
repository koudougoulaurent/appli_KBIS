#!/bin/bash

# ===========================================
# SYSTÈME DE SAUVEGARDE KBIS IMMOBILIER
# ===========================================
# Ce script crée des sauvegardes complètes avant chaque déploiement
# Usage: ./backup_system.sh [backup_type]
# Types: full, data, config, quick

set -e

# Configuration
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"
DB_FILE="$APP_DIR/db.sqlite3"
MEDIA_DIR="$APP_DIR/media"
STATIC_DIR="$APP_DIR/staticfiles"
CONFIG_FILES=(
    "/etc/nginx/sites-available/kbis-immobilier"
    "/etc/systemd/system/kbis-immobilier.service"
    "/var/www/kbis_immobilier/.env"
    "/var/www/kbis_immobilier/gunicorn.conf.py"
)

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

# Créer le répertoire de sauvegarde
create_backup_dir() {
    local backup_type=$1
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/${backup_type}_${timestamp}"
    
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# Sauvegarde complète
backup_full() {
    log "🔄 Début de la sauvegarde complète..."
    
    local backup_path=$(create_backup_dir "full")
    
    # Sauvegarder la base de données
    if [ -f "$DB_FILE" ]; then
        log "📊 Sauvegarde de la base de données..."
        cp "$DB_FILE" "$backup_path/db.sqlite3"
        log_success "Base de données sauvegardée"
    else
        log_warning "Base de données non trouvée: $DB_FILE"
    fi
    
    # Sauvegarder les médias
    if [ -d "$MEDIA_DIR" ]; then
        log "📁 Sauvegarde des fichiers média..."
        cp -r "$MEDIA_DIR" "$backup_path/"
        log_success "Fichiers média sauvegardés"
    fi
    
    # Sauvegarder les fichiers statiques
    if [ -d "$STATIC_DIR" ]; then
        log "🎨 Sauvegarde des fichiers statiques..."
        cp -r "$STATIC_DIR" "$backup_path/"
        log_success "Fichiers statiques sauvegardés"
    fi
    
    # Sauvegarder les fichiers de configuration
    log "⚙️  Sauvegarde des configurations..."
    mkdir -p "$backup_path/config"
    for config_file in "${CONFIG_FILES[@]}"; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "$backup_path/config/"
            log "  ✓ $(basename "$config_file")"
        fi
    done
    
    # Sauvegarder le code source (sans venv)
    log "💻 Sauvegarde du code source..."
    rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
          --exclude='.git' --exclude='db.sqlite3' --exclude='media' --exclude='staticfiles' \
          "$APP_DIR/" "$backup_path/code/"
    
    # Créer un fichier de métadonnées
    cat > "$backup_path/backup_info.txt" << EOF
Type: Sauvegarde complète
Date: $(date)
Commit: $(cd "$APP_DIR" && git rev-parse HEAD 2>/dev/null || echo "N/A")
Branche: $(cd "$APP_DIR" && git branch --show-current 2>/dev/null || echo "N/A")
Taille: $(du -sh "$backup_path" | cut -f1)
Utilisateur: $(whoami)
Hostname: $(hostname)
EOF
    
    log_success "Sauvegarde complète terminée: $backup_path"
    echo "$backup_path"
}

# Sauvegarde des données uniquement
backup_data() {
    log "🔄 Début de la sauvegarde des données..."
    
    local backup_path=$(create_backup_dir "data")
    
    # Base de données
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$backup_path/db.sqlite3"
        log_success "Base de données sauvegardée"
    fi
    
    # Fichiers média
    if [ -d "$MEDIA_DIR" ]; then
        cp -r "$MEDIA_DIR" "$backup_path/"
        log_success "Fichiers média sauvegardés"
    fi
    
    # Métadonnées
    cat > "$backup_path/backup_info.txt" << EOF
Type: Sauvegarde des données
Date: $(date)
Taille: $(du -sh "$backup_path" | cut -f1)
EOF
    
    log_success "Sauvegarde des données terminée: $backup_path"
    echo "$backup_path"
}

# Sauvegarde de configuration
backup_config() {
    log "🔄 Début de la sauvegarde des configurations..."
    
    local backup_path=$(create_backup_dir "config")
    
    # Fichiers de configuration
    mkdir -p "$backup_path"
    for config_file in "${CONFIG_FILES[@]}"; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "$backup_path/"
            log "  ✓ $(basename "$config_file")"
        fi
    done
    
    # Métadonnées
    cat > "$backup_path/backup_info.txt" << EOF
Type: Sauvegarde des configurations
Date: $(date)
EOF
    
    log_success "Sauvegarde des configurations terminée: $backup_path"
    echo "$backup_path"
}

# Sauvegarde rapide (base de données seulement)
backup_quick() {
    log "🔄 Début de la sauvegarde rapide..."
    
    local backup_path=$(create_backup_dir "quick")
    
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$backup_path/db.sqlite3"
        log_success "Sauvegarde rapide terminée: $backup_path"
        echo "$backup_path"
    else
        log_error "Base de données non trouvée: $DB_FILE"
        exit 1
    fi
}

# Nettoyer les anciennes sauvegardes (garder les 10 dernières)
cleanup_old_backups() {
    log "🧹 Nettoyage des anciennes sauvegardes..."
    
    # Garder les 10 dernières sauvegardes de chaque type
    for backup_type in full data config quick; do
        local count=$(ls -1 "$BACKUP_DIR" | grep "^${backup_type}_" | wc -l)
        if [ "$count" -gt 10 ]; then
            local to_delete=$((count - 10))
            ls -1t "$BACKUP_DIR" | grep "^${backup_type}_" | tail -n "$to_delete" | while read -r old_backup; do
                log "  🗑️  Suppression: $old_backup"
                rm -rf "$BACKUP_DIR/$old_backup"
            done
        fi
    done
    
    log_success "Nettoyage terminé"
}

# Lister les sauvegardes disponibles
list_backups() {
    log "📋 Sauvegardes disponibles:"
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
    local backup_type=${1:-"full"}
    
    # Créer le répertoire de sauvegarde principal
    mkdir -p "$BACKUP_DIR"
    
    case "$backup_type" in
        "full")
            backup_full
            ;;
        "data")
            backup_data
            ;;
        "config")
            backup_config
            ;;
        "quick")
            backup_quick
            ;;
        "list")
            list_backups
            exit 0
            ;;
        "cleanup")
            cleanup_old_backups
            exit 0
            ;;
        *)
            echo "Usage: $0 [full|data|config|quick|list|cleanup]"
            echo
            echo "Types de sauvegarde:"
            echo "  full    - Sauvegarde complète (base + média + statique + config + code)"
            echo "  data    - Données uniquement (base + média)"
            echo "  config  - Configurations uniquement"
            echo "  quick   - Base de données uniquement"
            echo "  list    - Lister les sauvegardes disponibles"
            echo "  cleanup - Nettoyer les anciennes sauvegardes"
            exit 1
            ;;
    esac
    
    # Nettoyer les anciennes sauvegardes après chaque sauvegarde
    cleanup_old_backups
}

# Exécution
main "$@"
