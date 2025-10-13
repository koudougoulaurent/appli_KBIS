#!/bin/bash

# ===========================================
# GESTION DE LA PERSISTANCE DES DONNÉES KBIS
# ===========================================
# Ce script assure la persistance et la protection des données critiques
# Usage: ./data_persistence.sh [action] [options]

set -e

# Configuration
APP_DIR="/var/www/kbis_immobilier"
DB_FILE="$APP_DIR/db.sqlite3"
MEDIA_DIR="$APP_DIR/media"
BACKUP_DIR="/var/backups/kbis_immobilier"
PERSISTENCE_DIR="/var/persistence/kbis_immobilier"
LOG_FILE="/var/log/kbis_persistence.log"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_success() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_warning() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_error() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

# Créer la structure de persistance
setup_persistence_structure() {
    log "🏗️  Configuration de la structure de persistance..."
    
    # Créer les répertoires de persistance
    mkdir -p "$PERSISTENCE_DIR"/{database,media,config,logs}
    mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Définir les permissions
    chown -R kbis:kbis "$PERSISTENCE_DIR"
    chown -R kbis:kbis "$BACKUP_DIR"
    chmod -R 755 "$PERSISTENCE_DIR"
    chmod -R 755 "$BACKUP_DIR"
    
    log_success "Structure de persistance créée"
}

# Vérifier l'intégrité des données
check_data_integrity() {
    log "🔍 Vérification de l'intégrité des données..."
    
    local all_good=true
    
    # Vérifier la base de données
    if [ -f "$DB_FILE" ]; then
        if sqlite3 "$DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
            log_success "Base de données: Intégrité OK"
        else
            log_error "Base de données: Problème d'intégrité détecté"
            all_good=false
        fi
        
        # Vérifier les tables critiques
        local critical_tables=(
            "django_migrations"
            "utilisateurs_utilisateur"
            "core_configurationentreprise"
            "proprietes_propriete"
            "contrats_contrat"
            "paiements_paiement"
        )
        
        for table in "${critical_tables[@]}"; do
            if sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';" | grep -q "$table"; then
                log_success "Table $table: Présente"
            else
                log_warning "Table $table: Manquante"
            fi
        done
    else
        log_error "Fichier de base de données non trouvé: $DB_FILE"
        all_good=false
    fi
    
    # Vérifier les fichiers média
    if [ -d "$MEDIA_DIR" ]; then
        local media_count=$(find "$MEDIA_DIR" -type f | wc -l)
        log_success "Fichiers média: $media_count fichiers"
    else
        log_warning "Répertoire média non trouvé: $MEDIA_DIR"
    fi
    
    if [ "$all_good" = true ]; then
        return 0
    else
        return 1
    fi
}

# Créer une sauvegarde de persistance
create_persistence_backup() {
    local backup_type=${1:-"daily"}
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/$backup_type/persistence_${timestamp}"
    
    log "💾 Création de la sauvegarde de persistance ($backup_type)..."
    
    mkdir -p "$backup_path"
    
    # Sauvegarder la base de données
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$backup_path/db.sqlite3"
        log_success "Base de données sauvegardée"
    fi
    
    # Sauvegarder les fichiers média
    if [ -d "$MEDIA_DIR" ]; then
        cp -r "$MEDIA_DIR" "$backup_path/"
        log_success "Fichiers média sauvegardés"
    fi
    
    # Sauvegarder les configurations
    local config_files=(
        "$APP_DIR/.env"
        "/etc/nginx/sites-available/kbis-immobilier"
        "/etc/systemd/system/kbis-immobilier.service"
    )
    
    mkdir -p "$backup_path/config"
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "$backup_path/config/"
        fi
    done
    
    # Créer un fichier de métadonnées
    cat > "$backup_path/backup_info.txt" << EOF
Type: Sauvegarde de persistance ($backup_type)
Date: $(date)
Taille: $(du -sh "$backup_path" | cut -f1)
Commit: $(cd "$APP_DIR" && git rev-parse HEAD 2>/dev/null || echo "N/A")
EOF
    
    log_success "Sauvegarde de persistance créée: $backup_path"
    echo "$backup_path"
}

# Synchroniser les données vers le répertoire de persistance
sync_to_persistence() {
    log "🔄 Synchronisation vers le répertoire de persistance..."
    
    # Synchroniser la base de données
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$PERSISTENCE_DIR/database/"
        log_success "Base de données synchronisée"
    fi
    
    # Synchroniser les fichiers média
    if [ -d "$MEDIA_DIR" ]; then
        rsync -av --delete "$MEDIA_DIR/" "$PERSISTENCE_DIR/media/"
        log_success "Fichiers média synchronisés"
    fi
    
    # Synchroniser les configurations
    local config_files=(
        "$APP_DIR/.env"
        "/etc/nginx/sites-available/kbis-immobilier"
        "/etc/systemd/system/kbis-immobilier.service"
    )
    
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "$PERSISTENCE_DIR/config/"
        fi
    done
    
    # Synchroniser les logs
    if [ -f "$LOG_FILE" ]; then
        cp "$LOG_FILE" "$PERSISTENCE_DIR/logs/"
    fi
    
    log_success "Synchronisation terminée"
}

# Restaurer depuis le répertoire de persistance
restore_from_persistence() {
    log "🔄 Restauration depuis le répertoire de persistance..."
    
    # Arrêter les services
    systemctl stop kbis-immobilier
    
    # Restaurer la base de données
    if [ -f "$PERSISTENCE_DIR/database/db.sqlite3" ]; then
        cp "$PERSISTENCE_DIR/database/db.sqlite3" "$DB_FILE"
        chown kbis:kbis "$DB_FILE"
        chmod 664 "$DB_FILE"
        log_success "Base de données restaurée"
    fi
    
    # Restaurer les fichiers média
    if [ -d "$PERSISTENCE_DIR/media" ]; then
        rm -rf "$MEDIA_DIR"
        cp -r "$PERSISTENCE_DIR/media" "$MEDIA_DIR"
        chown -R kbis:kbis "$MEDIA_DIR"
        log_success "Fichiers média restaurés"
    fi
    
    # Redémarrer les services
    systemctl start kbis-immobilier
    
    log_success "Restauration terminée"
}

# Nettoyer les anciennes sauvegardes
cleanup_old_backups() {
    log "🧹 Nettoyage des anciennes sauvegardes..."
    
    # Nettoyer les sauvegardes quotidiennes (garder 7 jours)
    find "$BACKUP_DIR/daily" -name "persistence_*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
    
    # Nettoyer les sauvegardes hebdomadaires (garder 4 semaines)
    find "$BACKUP_DIR/weekly" -name "persistence_*" -type d -mtime +28 -exec rm -rf {} \; 2>/dev/null || true
    
    # Nettoyer les sauvegardes mensuelles (garder 12 mois)
    find "$BACKUP_DIR/monthly" -name "persistence_*" -type d -mtime +365 -exec rm -rf {} \; 2>/dev/null || true
    
    log_success "Nettoyage terminé"
}

# Planifier les sauvegardes automatiques
schedule_automatic_backups() {
    log "⏰ Configuration des sauvegardes automatiques..."
    
    # Créer le script de sauvegarde quotidienne
    cat > /usr/local/bin/kbis-daily-backup.sh << 'EOF'
#!/bin/bash
cd /var/www/kbis_immobilier
./data_persistence.sh backup daily
EOF
    chmod +x /usr/local/bin/kbis-daily-backup.sh
    
    # Créer le script de sauvegarde hebdomadaire
    cat > /usr/local/bin/kbis-weekly-backup.sh << 'EOF'
#!/bin/bash
cd /var/www/kbis_immobilier
./data_persistence.sh backup weekly
EOF
    chmod +x /usr/local/bin/kbis-weekly-backup.sh
    
    # Créer le script de sauvegarde mensuelle
    cat > /usr/local/bin/kbis-monthly-backup.sh << 'EOF'
#!/bin/bash
cd /var/www/kbis_immobilier
./data_persistence.sh backup monthly
EOF
    chmod +x /usr/local/bin/kbis-monthly-backup.sh
    
    # Ajouter les tâches cron
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/kbis-daily-backup.sh") | crontab -
    (crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/local/bin/kbis-weekly-backup.sh") | crontab -
    (crontab -l 2>/dev/null; echo "0 4 1 * * /usr/local/bin/kbis-monthly-backup.sh") | crontab -
    
    log_success "Sauvegardes automatiques configurées"
}

# Surveiller l'espace disque
monitor_disk_space() {
    log "💾 Surveillance de l'espace disque..."
    
    local disk_usage=$(df "$APP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    local available_space=$(df "$APP_DIR" | awk 'NR==2 {print $4}')
    
    log "Utilisation: $disk_usage% (Espace disponible: $(($available_space / 1024)) MB)"
    
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Espace disque critique: $disk_usage% utilisé"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Espace disque élevé: $disk_usage% utilisé"
    else
        log_success "Espace disque OK: $disk_usage% utilisé"
    fi
    
    return 0
}

# Vérifier les permissions des fichiers critiques
check_file_permissions() {
    log "🔐 Vérification des permissions des fichiers critiques..."
    
    local all_good=true
    
    # Vérifier la base de données
    if [ -f "$DB_FILE" ]; then
        local perms=$(stat -c "%a" "$DB_FILE")
        if [ "$perms" = "664" ]; then
            log_success "Base de données: Permissions OK ($perms)"
        else
            log_warning "Base de données: Permissions incorrectes ($perms)"
            chmod 664 "$DB_FILE"
            all_good=false
        fi
        
        local owner=$(stat -c "%U:%G" "$DB_FILE")
        if [ "$owner" = "kbis:kbis" ]; then
            log_success "Base de données: Propriétaire OK ($owner)"
        else
            log_warning "Base de données: Propriétaire incorrect ($owner)"
            chown kbis:kbis "$DB_FILE"
            all_good=false
        fi
    fi
    
    # Vérifier les répertoires
    local dirs=("$MEDIA_DIR" "$APP_DIR/staticfiles")
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            local perms=$(stat -c "%a" "$dir")
            if [ "$perms" = "755" ]; then
                log_success "$(basename "$dir"): Permissions OK ($perms)"
            else
                log_warning "$(basename "$dir"): Permissions incorrectes ($perms)"
                chmod 755 "$dir"
                all_good=false
            fi
        fi
    done
    
    if [ "$all_good" = true ]; then
        return 0
    else
        return 1
    fi
}

# Afficher l'aide
show_help() {
    cat << EOF
Usage: $0 [action] [options]

Gestion de la persistance des données KBIS Immobilier.

ACTIONS:
  setup           Configurer la structure de persistance
  check           Vérifier l'intégrité des données
  backup [type]   Créer une sauvegarde (daily|weekly|monthly)
  sync            Synchroniser vers le répertoire de persistance
  restore         Restaurer depuis le répertoire de persistance
  cleanup         Nettoyer les anciennes sauvegardes
  schedule        Configurer les sauvegardes automatiques
  monitor         Surveiller l'espace disque
  permissions     Vérifier les permissions des fichiers
  status          Afficher le statut de la persistance

OPTIONS:
  --help          Afficher cette aide

EXEMPLES:
  $0 setup                    # Configuration initiale
  $0 backup daily             # Sauvegarde quotidienne
  $0 check                    # Vérification d'intégrité
  $0 sync                     # Synchronisation
  $0 schedule                 # Configuration des sauvegardes automatiques
EOF
}

# Afficher le statut
show_status() {
    log "📊 Statut de la persistance des données"
    echo
    
    # Base de données
    if [ -f "$DB_FILE" ]; then
        local db_size=$(du -h "$DB_FILE" | cut -f1)
        local db_perms=$(stat -c "%a" "$DB_FILE")
        echo "Base de données: $db_size ($db_perms)"
    else
        echo "Base de données: Non trouvée"
    fi
    
    # Fichiers média
    if [ -d "$MEDIA_DIR" ]; then
        local media_count=$(find "$MEDIA_DIR" -type f | wc -l)
        local media_size=$(du -sh "$MEDIA_DIR" | cut -f1)
        echo "Fichiers média: $media_count fichiers ($media_size)"
    else
        echo "Fichiers média: Non trouvé"
    fi
    
    # Sauvegardes
    local daily_backups=$(find "$BACKUP_DIR/daily" -name "persistence_*" -type d 2>/dev/null | wc -l)
    local weekly_backups=$(find "$BACKUP_DIR/weekly" -name "persistence_*" -type d 2>/dev/null | wc -l)
    local monthly_backups=$(find "$BACKUP_DIR/monthly" -name "persistence_*" -type d 2>/dev/null | wc -l)
    echo "Sauvegardes: $daily_backups quotidiennes, $weekly_backups hebdomadaires, $monthly_backups mensuelles"
    
    # Espace disque
    local disk_usage=$(df "$APP_DIR" | awk 'NR==2 {print $5}')
    echo "Espace disque: $disk_usage% utilisé"
    
    # Tâches cron
    if crontab -l 2>/dev/null | grep -q "kbis.*backup"; then
        echo "Sauvegardes automatiques: Configurées"
    else
        echo "Sauvegardes automatiques: Non configurées"
    fi
}

# Fonction principale
main() {
    local action=$1
    local option=$2
    
    # Créer le répertoire de logs
    mkdir -p "$(dirname "$LOG_FILE")"
    
    case "$action" in
        "setup")
            setup_persistence_structure
            ;;
        "check")
            check_data_integrity
            ;;
        "backup")
            create_persistence_backup "${option:-daily}"
            ;;
        "sync")
            sync_to_persistence
            ;;
        "restore")
            restore_from_persistence
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "schedule")
            schedule_automatic_backups
            ;;
        "monitor")
            monitor_disk_space
            ;;
        "permissions")
            check_file_permissions
            ;;
        "status")
            show_status
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Action inconnue: $action"
            show_help
            exit 1
            ;;
    esac
}

# Exécution
main "$@"
