#!/bin/bash

# =============================================================================
# SCRIPT DE MISE À JOUR SÉCURISÉE DEPUIS LA BRANCHE modifications-octobre-2025
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
BRANCH="modifications-octobre-2025"
BACKUP_DIR="/var/backups/$APP_NAME"
LOG_FILE="/var/log/$APP_NAME/update.log"
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

# Fonction de sauvegarde
backup_database() {
    local backup_file="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log "📦 Création de la sauvegarde de la base de données..."
    
    # Créer le répertoire de sauvegarde s'il n'existe pas
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder la base de données
    if sudo -u postgres pg_dump kbis_immobilier > "$backup_file" 2>/dev/null; then
        log_success "Sauvegarde créée: $backup_file"
        echo "$backup_file" > "$BACKUP_DIR/latest_backup.txt"
        return 0
    else
        log_error "Échec de la sauvegarde de la base de données"
        return 1
    fi
}

# Fonction de test des migrations
test_migrations() {
    log "🧪 Test des migrations en mode dry-run..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    if python manage.py migrate --dry-run --verbosity=0; then
        log_success "Test des migrations réussi"
        return 0
    else
        log_error "Échec du test des migrations"
        return 1
    fi
}

# Fonction de mise à jour
update_application() {
    log "🔄 Mise à jour de l'application depuis la branche $BRANCH..."
    
    cd "$APP_DIR"
    
    # Arrêter les services
    log "⏹️  Arrêt des services..."
    sudo systemctl stop kbis_immobilier || true
    
    # Sauvegarder la configuration actuelle
    cp -r "$APP_DIR" "$BACKUP_DIR/app_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Récupérer les dernières modifications
    log "📥 Récupération des modifications depuis GitHub..."
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    
    # Mettre à jour les dépendances
    log "📦 Mise à jour des dépendances..."
    source venv/bin/activate
    pip install -r requirements.txt --upgrade
    
    # Installer les nouvelles dépendances pour l'export
    log "📦 Installation des dépendances d'export..."
    pip install openpyxl==3.1.5 reportlab==4.4.3
    
    # Appliquer les migrations
    log "🗄️  Application des migrations..."
    python manage.py migrate
    
    # Collecter les fichiers statiques
    log "📁 Collection des fichiers statiques..."
    python manage.py collectstatic --noinput
    
    # Redémarrer les services
    log "▶️  Redémarrage des services..."
    sudo systemctl start kbis_immobilier
    sudo systemctl reload nginx
    
    # Attendre que les services démarrent
    sleep 5
    
    # Vérifier le statut des services
    if systemctl is-active --quiet kbis_immobilier && systemctl is-active --quiet nginx; then
        log_success "Services redémarrés avec succès"
        return 0
    else
        log_error "Échec du redémarrage des services"
        return 1
    fi
}

# Fonction de vérification
verify_deployment() {
    log "🔍 Vérification du déploiement..."
    
    # Test de connectivité
    if curl -f -s http://localhost > /dev/null; then
        log_success "Application accessible localement"
    else
        log_error "Application non accessible localement"
        return 1
    fi
    
    # Test de la base de données
    cd "$APP_DIR"
    source venv/bin/activate
    if python manage.py check --deploy; then
        log_success "Vérification Django réussie"
    else
        log_warning "Avertissements lors de la vérification Django"
    fi
    
    # Test des logs
    if [ -f "$LOG_FILE" ]; then
        log_success "Logs disponibles: $LOG_FILE"
    fi
    
    return 0
}

# Fonction de nettoyage des anciennes sauvegardes
cleanup_old_backups() {
    log "🧹 Nettoyage des anciennes sauvegardes..."
    
    # Garder seulement les 5 dernières sauvegardes
    find "$BACKUP_DIR" -name "db_backup_*.sql" -type f -mtime +7 -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "app_backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Nettoyage terminé"
}

# Fonction principale
main() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "🚀 MISE À JOUR SÉCURISÉE DE L'APPLICATION KBIS IMMOBILIER"
    echo "📅 $(date)"
    echo "🌿 Branche: $BRANCH"
    echo "============================================================================="
    echo -e "${NC}"
    
    # Créer le répertoire de logs
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Envoyer notification de début
    send_notification "KBIS - Début de mise à jour" "Mise à jour démarrée depuis la branche $BRANCH"
    
    # 1. Sauvegarde
    if ! backup_database; then
        log_error "Échec de la sauvegarde. Arrêt de la mise à jour."
        send_notification "KBIS - Échec mise à jour" "Échec de la sauvegarde. Mise à jour annulée."
        exit 1
    fi
    
    # 2. Test des migrations
    if ! test_migrations; then
        log_error "Échec du test des migrations. Arrêt de la mise à jour."
        send_notification "KBIS - Échec mise à jour" "Échec du test des migrations. Mise à jour annulée."
        exit 1
    fi
    
    # 3. Mise à jour
    if ! update_application; then
        log_error "Échec de la mise à jour. Restauration en cours..."
        send_notification "KBIS - Échec mise à jour" "Échec de la mise à jour. Restauration en cours."
        # Ici on pourrait appeler le script de rollback
        exit 1
    fi
    
    # 4. Vérification
    if ! verify_deployment; then
        log_error "Échec de la vérification. Restauration en cours..."
        send_notification "KBIS - Échec vérification" "Échec de la vérification. Restauration en cours."
        exit 1
    fi
    
    # 5. Nettoyage
    cleanup_old_backups
    
    # 6. Notification de succès
    log_success "🎉 Mise à jour terminée avec succès !"
    send_notification "KBIS - Mise à jour réussie" "Mise à jour terminée avec succès depuis la branche $BRANCH"
    
    echo -e "${GREEN}"
    echo "============================================================================="
    echo "✅ MISE À JOUR TERMINÉE AVEC SUCCÈS !"
    echo "📅 $(date)"
    echo "🌿 Branche: $BRANCH"
    echo "📊 Logs: $LOG_FILE"
    echo "📦 Sauvegarde: $(cat $BACKUP_DIR/latest_backup.txt 2>/dev/null || echo 'Non disponible')"
    echo "============================================================================="
    echo -e "${NC}"
}

# Exécution
main "$@"





