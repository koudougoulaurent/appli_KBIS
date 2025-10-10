#!/bin/bash

# =============================================================================
# SCRIPT DE ROLLBACK AUTOMATIQUE EN CAS DE PROBLÈME
# =============================================================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="kbis_immobilier"
APP_DIR="/var/www/$APP_NAME"
BACKUP_DIR="/var/backups/$APP_NAME"
LOG_FILE="/var/log/$APP_NAME/rollback.log"
NOTIFICATION_EMAIL="admin@votre-domaine.com"  # Changez cette adresse

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Fonction de notification
send_notification() {
    local subject="$1"
    local message="$2"
    
    # Notification par email (si mailutils est installé)
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$NOTIFICATION_EMAIL" 2>/dev/null || true
    fi
    
    # Notification dans les logs système
    logger -t "$APP_NAME" "$subject: $message"
    
    # Notification par wall (si des utilisateurs sont connectés)
    echo "$subject: $message" | wall 2>/dev/null || true
}

# Fonction d'affichage des sauvegardes disponibles
list_backups() {
    echo -e "${CYAN}📦 Sauvegardes disponibles :${NC}"
    echo "=================================="
    
    if [ -d "$BACKUP_DIR" ]; then
        # Sauvegardes de base de données
        echo -e "${YELLOW}🗄️  Sauvegardes de base de données :${NC}"
        ls -la "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | tail -5 || echo "Aucune sauvegarde de DB trouvée"
        
        echo ""
        echo -e "${YELLOW}📁 Sauvegardes d'application :${NC}"
        ls -la "$BACKUP_DIR"/app_backup_* 2>/dev/null | tail -5 || echo "Aucune sauvegarde d'app trouvée"
    else
        echo "Aucune sauvegarde trouvée dans $BACKUP_DIR"
    fi
}

# Fonction de rollback de la base de données
rollback_database() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        # Utiliser la dernière sauvegarde
        backup_file=$(cat "$BACKUP_DIR/latest_backup.txt" 2>/dev/null || echo "")
    fi
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        log_error "Aucune sauvegarde de base de données valide trouvée"
        return 1
    fi
    
    log "🔄 Restauration de la base de données depuis: $backup_file"
    
    # Arrêter l'application
    sudo systemctl stop kbis_immobilier || true
    
    # Restaurer la base de données
    if sudo -u postgres psql -c "DROP DATABASE IF EXISTS kbis_immobilier;" 2>/dev/null; then
        log "🗑️  Ancienne base de données supprimée"
    fi
    
    if sudo -u postgres psql -c "CREATE DATABASE kbis_immobilier;" 2>/dev/null; then
        log "📦 Nouvelle base de données créée"
    fi
    
    if sudo -u postgres psql kbis_immobilier < "$backup_file" 2>/dev/null; then
        log_success "Base de données restaurée avec succès"
        return 0
    else
        log_error "Échec de la restauration de la base de données"
        return 1
    fi
}

# Fonction de rollback de l'application
rollback_application() {
    local backup_dir="$1"
    
    if [ -z "$backup_dir" ]; then
        # Utiliser la dernière sauvegarde d'application
        backup_dir=$(ls -td "$BACKUP_DIR"/app_backup_* 2>/dev/null | head -1 || echo "")
    fi
    
    if [ -z "$backup_dir" ] || [ ! -d "$backup_dir" ]; then
        log_error "Aucune sauvegarde d'application valide trouvée"
        return 1
    fi
    
    log "🔄 Restauration de l'application depuis: $backup_dir"
    
    # Arrêter les services
    sudo systemctl stop kbis_immobilier || true
    
    # Sauvegarder l'état actuel (au cas où)
    cp -r "$APP_DIR" "$APP_DIR.broken.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Restaurer l'application
    if rm -rf "$APP_DIR" && cp -r "$backup_dir" "$APP_DIR"; then
        log_success "Application restaurée avec succès"
        
        # Restaurer les permissions
        chown -R www-data:www-data "$APP_DIR"
        chmod -R 755 "$APP_DIR"
        
        return 0
    else
        log_error "Échec de la restauration de l'application"
        return 1
    fi
}

# Fonction de redémarrage des services
restart_services() {
    log "🔄 Redémarrage des services..."
    
    # Redémarrer Gunicorn
    if sudo systemctl start kbis_immobilier; then
        log_success "Service kbis_immobilier redémarré"
    else
        log_error "Échec du redémarrage de kbis_immobilier"
        return 1
    fi
    
    # Recharger Nginx
    if sudo systemctl reload nginx; then
        log_success "Nginx rechargé"
    else
        log_warning "Problème lors du rechargement de Nginx"
    fi
    
    # Attendre que les services démarrent
    sleep 5
    
    # Vérifier le statut
    if systemctl is-active --quiet kbis_immobilier && systemctl is-active --quiet nginx; then
        log_success "Services redémarrés avec succès"
        return 0
    else
        log_error "Problème avec les services après redémarrage"
        return 1
    fi
}

# Fonction de vérification post-rollback
verify_rollback() {
    log "🔍 Vérification du rollback..."
    
    # Test de connectivité
    if curl -f -s http://localhost > /dev/null; then
        log_success "Application accessible après rollback"
    else
        log_error "Application non accessible après rollback"
        return 1
    fi
    
    # Test de la base de données
    cd "$APP_DIR"
    source venv/bin/activate
    if python manage.py check --deploy; then
        log_success "Vérification Django réussie après rollback"
    else
        log_warning "Avertissements lors de la vérification Django après rollback"
    fi
    
    return 0
}

# Fonction de rollback complet
full_rollback() {
    local db_backup="$1"
    local app_backup="$2"
    
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "🔄 ROLLBACK COMPLET DE L'APPLICATION KBIS IMMOBILIER"
    echo "📅 $(date)"
    echo "============================================================================="
    echo -e "${NC}"
    
    # Créer le répertoire de logs
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Envoyer notification de début
    send_notification "KBIS - Début de rollback" "Rollback démarré"
    
    # 1. Rollback de la base de données
    if ! rollback_database "$db_backup"; then
        log_error "Échec du rollback de la base de données"
        send_notification "KBIS - Échec rollback" "Échec du rollback de la base de données"
        exit 1
    fi
    
    # 2. Rollback de l'application
    if ! rollback_application "$app_backup"; then
        log_error "Échec du rollback de l'application"
        send_notification "KBIS - Échec rollback" "Échec du rollback de l'application"
        exit 1
    fi
    
    # 3. Redémarrage des services
    if ! restart_services; then
        log_error "Échec du redémarrage des services"
        send_notification "KBIS - Échec rollback" "Échec du redémarrage des services"
        exit 1
    fi
    
    # 4. Vérification
    if ! verify_rollback; then
        log_error "Échec de la vérification après rollback"
        send_notification "KBIS - Échec rollback" "Échec de la vérification après rollback"
        exit 1
    fi
    
    # 5. Notification de succès
    log_success "🎉 Rollback terminé avec succès !"
    send_notification "KBIS - Rollback réussi" "Rollback terminé avec succès"
    
    echo -e "${GREEN}"
    echo "============================================================================="
    echo "✅ ROLLBACK TERMINÉ AVEC SUCCÈS !"
    echo "📅 $(date)"
    echo "📊 Logs: $LOG_FILE"
    echo "============================================================================="
    echo -e "${NC}"
}

# Fonction d'aide
show_help() {
    echo -e "${CYAN}Usage: $0 [OPTIONS]${NC}"
    echo ""
    echo "Options:"
    echo "  -h, --help              Afficher cette aide"
    echo "  -l, --list              Lister les sauvegardes disponibles"
    echo "  -d, --db-backup FILE    Spécifier un fichier de sauvegarde de DB"
    echo "  -a, --app-backup DIR    Spécifier un répertoire de sauvegarde d'app"
    echo "  --db-only               Rollback de la base de données seulement"
    echo "  --app-only              Rollback de l'application seulement"
    echo ""
    echo "Exemples:"
    echo "  $0                      # Rollback complet avec les dernières sauvegardes"
    echo "  $0 -l                   # Lister les sauvegardes disponibles"
    echo "  $0 -d /path/to/db.sql   # Rollback avec une sauvegarde DB spécifique"
    echo "  $0 --db-only            # Rollback de la DB seulement"
}

# Fonction principale
main() {
    local db_backup=""
    local app_backup=""
    local db_only=false
    local app_only=false
    
    # Parse des arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--list)
                list_backups
                exit 0
                ;;
            -d|--db-backup)
                db_backup="$2"
                shift 2
                ;;
            -a|--app-backup)
                app_backup="$2"
                shift 2
                ;;
            --db-only)
                db_only=true
                shift
                ;;
            --app-only)
                app_only=true
                shift
                ;;
            *)
                echo "Option inconnue: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Exécution selon les options
    if [ "$db_only" = true ]; then
        rollback_database "$db_backup"
    elif [ "$app_only" = true ]; then
        rollback_application "$app_backup"
    else
        full_rollback "$db_backup" "$app_backup"
    fi
}

# Exécution
main "$@"
