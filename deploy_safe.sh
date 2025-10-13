#!/bin/bash

# ===========================================
# DÉPLOIEMENT SÉCURISÉ KBIS IMMOBILIER
# ===========================================
# Ce script effectue un déploiement sécurisé avec sauvegardes et vérifications
# Usage: ./deploy_safe.sh [commit_hash] [options]

set -e

# Configuration
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"
SERVICE_NAME="kbis-immobilier"
REPO_URL="https://github.com/koudougoulaurent/appli_KBIS.git"
BRANCH="modifications-octobre-2025"
HEALTH_CHECK_TIMEOUT=300  # 5 minutes

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

# Afficher l'aide
show_help() {
    cat << EOF
Usage: $0 [commit_hash] [options]

Déploiement sécurisé de KBIS Immobilier avec sauvegardes automatiques et vérifications.

ARGUMENTS:
  commit_hash    Hash du commit à déployer (optionnel, défaut: HEAD de la branche)

OPTIONS:
  --no-backup    Ne pas créer de sauvegarde avant déploiement
  --no-rollback  Ne pas permettre le rollback automatique en cas d'échec
  --force        Forcer le déploiement même si des vérifications échouent
  --dry-run      Mode simulation (aucune modification)
  --help         Afficher cette aide

EXEMPLES:
  $0                           # Déploiement de la dernière version
  $0 abc123                    # Déploiement du commit abc123
  $0 --dry-run                 # Simulation du déploiement
  $0 --no-backup --force       # Déploiement sans sauvegarde

SÉCURITÉ:
  - Sauvegarde automatique avant déploiement
  - Vérifications de santé après déploiement
  - Rollback automatique en cas d'échec
  - Logs détaillés de toutes les opérations
EOF
}

# Vérifier les prérequis
check_prerequisites() {
    log "🔍 Vérification des prérequis..."
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -d "$APP_DIR" ]; then
        log_error "Répertoire de l'application non trouvé: $APP_DIR"
        exit 1
    fi
    
    # Vérifier que les scripts de sécurité existent
    local required_scripts=("backup_system.sh" "rollback_system.sh" "health_monitor.sh")
    for script in "${required_scripts[@]}"; do
        if [ ! -f "./$script" ]; then
            log_error "Script requis non trouvé: $script"
            exit 1
        fi
        if [ ! -x "./$script" ]; then
            log_warning "Rendre $script exécutable..."
            chmod +x "./$script"
        fi
    done
    
    # Vérifier l'espace disque
    local available_space=$(df "$APP_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1000000 ]; then  # 1GB en KB
        log_warning "Espace disque faible: $(df -h "$APP_DIR" | awk 'NR==2 {print $4}') disponible"
    fi
    
    log_success "Prérequis vérifiés"
}

# Créer une sauvegarde de sécurité
create_safety_backup() {
    log "💾 Création de la sauvegarde de sécurité..."
    
    if [ -f "./backup_system.sh" ]; then
        local backup_path=$(./backup_system.sh full)
        log_success "Sauvegarde créée: $backup_path"
        echo "$backup_path"
    else
        log_error "Script de sauvegarde non trouvé"
        exit 1
    fi
}

# Vérifier l'état actuel du service
check_current_status() {
    log "🔍 Vérification de l'état actuel du service..."
    
    local status_ok=true
    
    # Vérifier le service
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_warning "Service $SERVICE_NAME n'est pas actif"
        status_ok=false
    fi
    
    # Vérifier la connectivité
    if ! curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
        log_warning "Service non accessible via HTTP"
        status_ok=false
    fi
    
    if [ "$status_ok" = true ]; then
        log_success "Service actuel opérationnel"
        return 0
    else
        log_warning "Service actuel a des problèmes"
        return 1
    fi
}

# Mettre à jour le code source
update_source_code() {
    local commit_hash=$1
    local dry_run=$2
    
    log "📥 Mise à jour du code source..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune modification du code"
        return 0
    fi
    
    cd "$APP_DIR"
    
    # Sauvegarder l'état actuel
    local current_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    log "Commit actuel: $current_commit"
    
    # Récupérer les dernières modifications
    log "Récupération des dernières modifications..."
    git fetch origin "$BRANCH"
    
    # Vérifier que le commit existe
    if [ -n "$commit_hash" ]; then
        if ! git cat-file -e "$commit_hash" 2>/dev/null; then
            log_error "Commit non trouvé: $commit_hash"
            exit 1
        fi
        log "Déploiement du commit: $commit_hash"
        git checkout "$commit_hash"
    else
        log "Déploiement de la dernière version de la branche $BRANCH"
        git checkout "origin/$BRANCH"
    fi
    
    # Vérifier les changements
    local new_commit=$(git rev-parse HEAD)
    log "Nouveau commit: $new_commit"
    
    if [ "$current_commit" = "$new_commit" ]; then
        log_warning "Aucun changement détecté"
    fi
    
    log_success "Code source mis à jour"
}

# Mettre à jour les dépendances
update_dependencies() {
    local dry_run=$1
    
    log "📦 Mise à jour des dépendances..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune mise à jour des dépendances"
        return 0
    fi
    
    cd "$APP_DIR"
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Mettre à jour pip
    pip install --upgrade pip
    
    # Installer/mettre à jour les dépendances
    if [ -f "requirements.txt" ]; then
        log "Installation des dépendances depuis requirements.txt..."
        pip install -r requirements.txt
    fi
    
    log_success "Dépendances mises à jour"
}

# Appliquer les migrations
apply_migrations() {
    local dry_run=$1
    
    log "🗄️  Application des migrations..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune migration appliquée"
        return 0
    fi
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Vérifier les migrations en attente
    local pending_migrations=$(python manage.py showmigrations --plan | grep "\[ \]" | wc -l)
    if [ "$pending_migrations" -eq 0 ]; then
        log_success "Aucune migration en attente"
        return 0
    fi
    
    log "Application de $pending_migrations migration(s)..."
    python manage.py migrate
    
    log_success "Migrations appliquées"
}

# Collecter les fichiers statiques
collect_static_files() {
    local dry_run=$1
    
    log "🎨 Collecte des fichiers statiques..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune collecte de fichiers statiques"
        return 0
    fi
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Créer le répertoire staticfiles s'il n'existe pas
    mkdir -p staticfiles
    
    # Collecter les fichiers statiques
    python manage.py collectstatic --noinput
    
    # Vérifier les permissions
    chown -R kbis:kbis staticfiles/
    chmod -R 755 staticfiles/
    
    log_success "Fichiers statiques collectés"
}

# Redémarrer les services
restart_services() {
    local dry_run=$1
    
    log "🔄 Redémarrage des services..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucun redémarrage de service"
        return 0
    fi
    
    # Redémarrer le service Django
    systemctl restart "$SERVICE_NAME"
    sleep 3
    
    # Vérifier que le service est actif
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Service $SERVICE_NAME redémarré"
    else
        log_error "Échec du redémarrage du service $SERVICE_NAME"
        systemctl status "$SERVICE_NAME"
        return 1
    fi
    
    # Redémarrer Nginx
    systemctl reload nginx
    log_success "Nginx rechargé"
}

# Vérifier la santé du service après déploiement
verify_deployment() {
    local dry_run=$1
    
    log "🏥 Vérification de la santé du service..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucune vérification de santé"
        return 0
    fi
    
    # Attendre que le service soit prêt
    log "Attente de la disponibilité du service..."
    local max_wait=$HEALTH_CHECK_TIMEOUT
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
            log_success "Service accessible"
            break
        else
            log "Attente... ($waited/$max_wait secondes)"
            sleep 5
            waited=$((waited + 5))
        fi
    done
    
    if [ $waited -ge $max_wait ]; then
        log_error "Service non accessible après $max_wait secondes"
        return 1
    fi
    
    # Exécuter les vérifications de santé
    if [ -f "./health_monitor.sh" ]; then
        if ./health_monitor.sh quick; then
            log_success "Vérifications de santé passées"
            return 0
        else
            log_error "Échec des vérifications de santé"
            return 1
        fi
    else
        log_warning "Script de vérification de santé non trouvé"
        return 0
    fi
}

# Effectuer un rollback en cas d'échec
perform_rollback() {
    local backup_path=$1
    local dry_run=$2
    
    log "🔄 Rollback en cours..."
    
    if [ "$dry_run" = "true" ]; then
        log "🔍 Mode simulation - Aucun rollback effectué"
        return 0
    fi
    
    if [ -f "./rollback_system.sh" ] && [ -n "$backup_path" ]; then
        local backup_name=$(basename "$backup_path")
        if ./rollback_system.sh "$backup_name"; then
            log_success "Rollback effectué avec succès"
            return 0
        else
            log_error "Échec du rollback"
            return 1
        fi
    else
        log_error "Impossible d'effectuer le rollback"
        return 1
    fi
}

# Nettoyer les anciennes sauvegardes
cleanup_old_backups() {
    log "🧹 Nettoyage des anciennes sauvegardes..."
    
    if [ -f "./backup_system.sh" ]; then
        ./backup_system.sh cleanup
    fi
    
    log_success "Nettoyage terminé"
}

# Fonction principale
main() {
    local commit_hash=""
    local no_backup=false
    local no_rollback=false
    local force=false
    local dry_run=false
    local backup_path=""
    
    # Parser les arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                no_backup=true
                shift
                ;;
            --no-rollback)
                no_rollback=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Option inconnue: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$commit_hash" ]; then
                    commit_hash="$1"
                else
                    log_error "Trop d'arguments: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Afficher les paramètres
    log "🚀 Début du déploiement sécurisé"
    log "Commit: ${commit_hash:-"HEAD de $BRANCH"}"
    log "Mode simulation: $dry_run"
    log "Sauvegarde: $([ "$no_backup" = true ] && echo "Désactivée" || echo "Activée")"
    log "Rollback: $([ "$no_rollback" = true ] && echo "Désactivé" || echo "Activé")"
    log "Force: $force"
    echo
    
    # Vérifier les prérequis
    check_prerequisites
    
    # Vérifier l'état actuel
    if ! check_current_status && [ "$force" = false ]; then
        log_error "Service actuel non opérationnel. Utilisez --force pour continuer."
        exit 1
    fi
    
    # Créer une sauvegarde de sécurité
    if [ "$no_backup" = false ]; then
        backup_path=$(create_safety_backup)
    fi
    
    # Déploiement
    local deployment_success=true
    
    if update_source_code "$commit_hash" "$dry_run"; then
        log_success "Code source mis à jour"
    else
        log_error "Échec de la mise à jour du code source"
        deployment_success=false
    fi
    
    if [ "$deployment_success" = true ] && update_dependencies "$dry_run"; then
        log_success "Dépendances mises à jour"
    else
        log_error "Échec de la mise à jour des dépendances"
        deployment_success=false
    fi
    
    if [ "$deployment_success" = true ] && apply_migrations "$dry_run"; then
        log_success "Migrations appliquées"
    else
        log_error "Échec des migrations"
        deployment_success=false
    fi
    
    if [ "$deployment_success" = true ] && collect_static_files "$dry_run"; then
        log_success "Fichiers statiques collectés"
    else
        log_error "Échec de la collecte des fichiers statiques"
        deployment_success=false
    fi
    
    if [ "$deployment_success" = true ] && restart_services "$dry_run"; then
        log_success "Services redémarrés"
    else
        log_error "Échec du redémarrage des services"
        deployment_success=false
    fi
    
    # Vérification finale
    if [ "$deployment_success" = true ] && verify_deployment "$dry_run"; then
        log_success "Déploiement réussi et vérifié"
        cleanup_old_backups
    else
        log_error "Échec de la vérification du déploiement"
        deployment_success=false
    fi
    
    # Rollback si nécessaire
    if [ "$deployment_success" = false ] && [ "$no_rollback" = false ] && [ "$dry_run" = false ]; then
        log "🔄 Tentative de rollback..."
        if perform_rollback "$backup_path" "$dry_run"; then
            log_success "Rollback effectué avec succès"
        else
            log_error "Échec du rollback - Intervention manuelle requise"
            exit 1
        fi
    elif [ "$deployment_success" = false ]; then
        log_error "Déploiement échoué"
        exit 1
    fi
    
    log_success "Déploiement sécurisé terminé avec succès!"
}

# Exécution
main "$@"
