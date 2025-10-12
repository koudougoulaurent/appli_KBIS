#!/bin/bash

# Script de maintenance pour KBIS Immobilier
# Gestion des mises à jour, sauvegardes et monitoring

set -e

# Variables
APP_NAME="kbis-immobilier"
APP_USER="kbis"
APP_DIR="/home/$APP_USER/appli_KBIS"
BACKUP_DIR="/home/$APP_USER/backups"
SERVICE_NAME="kbis-immobilier"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction d'aide
show_help() {
    echo "Script de maintenance pour KBIS Immobilier"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  update          Mettre à jour l'application"
    echo "  backup          Créer une sauvegarde"
    echo "  restore         Restaurer depuis une sauvegarde"
    echo "  status          Afficher le statut des services"
    echo "  logs            Afficher les logs"
    echo "  restart         Redémarrer l'application"
    echo "  migrate         Exécuter les migrations"
    echo "  collectstatic   Collecter les fichiers statiques"
    echo "  shell           Ouvrir le shell Django"
    echo "  help            Afficher cette aide"
}

# Mise à jour de l'application
update_app() {
    log_info "Mise à jour de l'application..."
    
    cd $APP_DIR
    
    # Sauvegarde avant mise à jour
    log_info "Création d'une sauvegarde avant mise à jour..."
    $0 backup
    
    # Mise à jour du code
    log_info "Mise à jour du code depuis Git..."
    git fetch origin
    git checkout modifications-octobre-2025
    git pull origin modifications-octobre-2025
    
    # Activation de l'environnement virtuel
    source venv/bin/activate
    
    # Mise à jour des dépendances
    log_info "Mise à jour des dépendances..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Migration de la base de données
    log_info "Exécution des migrations..."
    python manage.py migrate
    
    # Collecte des fichiers statiques
    log_info "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    
    # Redémarrage de l'application
    log_info "Redémarrage de l'application..."
    sudo systemctl restart $SERVICE_NAME
    
    log_success "Mise à jour terminée !"
}

# Création d'une sauvegarde
backup_app() {
    log_info "Création d'une sauvegarde..."
    
    # Création du répertoire de sauvegarde
    mkdir -p $BACKUP_DIR
    
    # Nom du fichier de sauvegarde
    BACKUP_FILE="kbis_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    # Sauvegarde de la base de données
    log_info "Sauvegarde de la base de données..."
    sudo -u postgres pg_dump kbis_immobilier > $BACKUP_DIR/kbis_db_$(date +%Y%m%d_%H%M%S).sql
    
    # Sauvegarde des fichiers
    log_info "Sauvegarde des fichiers..."
    tar -czf $BACKUP_DIR/$BACKUP_FILE \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.git' \
        --exclude='logs' \
        $APP_DIR
    
    # Nettoyage des anciennes sauvegardes (garde les 7 dernières)
    log_info "Nettoyage des anciennes sauvegardes..."
    find $BACKUP_DIR -name "kbis_backup_*.tar.gz" -mtime +7 -delete
    find $BACKUP_DIR -name "kbis_db_*.sql" -mtime +7 -delete
    
    log_success "Sauvegarde créée: $BACKUP_FILE"
}

# Restauration depuis une sauvegarde
restore_app() {
    log_info "Sélection d'une sauvegarde à restaurer..."
    
    # Liste des sauvegardes disponibles
    echo "Sauvegardes disponibles:"
    ls -la $BACKUP_DIR/kbis_backup_*.tar.gz 2>/dev/null || {
        log_error "Aucune sauvegarde trouvée"
        exit 1
    }
    
    read -p "Entrez le nom du fichier de sauvegarde: " BACKUP_FILE
    
    if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        log_error "Fichier de sauvegarde non trouvé"
        exit 1
    fi
    
    # Arrêt de l'application
    log_info "Arrêt de l'application..."
    sudo systemctl stop $SERVICE_NAME
    
    # Sauvegarde de l'état actuel
    log_info "Sauvegarde de l'état actuel..."
    $0 backup
    
    # Restauration des fichiers
    log_info "Restauration des fichiers..."
    cd $APP_DIR
    tar -xzf $BACKUP_DIR/$BACKUP_FILE --strip-components=1
    
    # Redémarrage de l'application
    log_info "Redémarrage de l'application..."
    sudo systemctl start $SERVICE_NAME
    
    log_success "Restauration terminée !"
}

# Affichage du statut des services
show_status() {
    log_info "Statut des services:"
    echo ""
    
    # Statut de l'application
    echo "=== Application Django ==="
    sudo systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    
    # Statut de Nginx
    echo "=== Nginx ==="
    sudo systemctl status nginx --no-pager -l
    echo ""
    
    # Statut de PostgreSQL
    echo "=== PostgreSQL ==="
    sudo systemctl status postgresql --no-pager -l
    echo ""
    
    # Utilisation des ressources
    echo "=== Ressources système ==="
    echo "Mémoire:"
    free -h
    echo ""
    echo "Disque:"
    df -h
    echo ""
    echo "Processus:"
    ps aux | grep -E "(gunicorn|nginx|postgres)" | grep -v grep
}

# Affichage des logs
show_logs() {
    log_info "Logs de l'application (Ctrl+C pour quitter):"
    sudo journalctl -u $SERVICE_NAME -f
}

# Redémarrage de l'application
restart_app() {
    log_info "Redémarrage de l'application..."
    sudo systemctl restart $SERVICE_NAME
    sudo systemctl restart nginx
    log_success "Application redémarrée !"
}

# Exécution des migrations
run_migrations() {
    log_info "Exécution des migrations..."
    cd $APP_DIR
    source venv/bin/activate
    python manage.py migrate
    log_success "Migrations exécutées !"
}

# Collecte des fichiers statiques
collect_static() {
    log_info "Collecte des fichiers statiques..."
    cd $APP_DIR
    source venv/bin/activate
    python manage.py collectstatic --noinput
    log_success "Fichiers statiques collectés !"
}

# Shell Django
django_shell() {
    log_info "Ouverture du shell Django..."
    cd $APP_DIR
    source venv/bin/activate
    python manage.py shell
}

# Script principal
case "${1:-help}" in
    update)
        update_app
        ;;
    backup)
        backup_app
        ;;
    restore)
        restore_app
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    restart)
        restart_app
        ;;
    migrate)
        run_migrations
        ;;
    collectstatic)
        collect_static
        ;;
    shell)
        django_shell
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Commande inconnue: $1"
        show_help
        exit 1
        ;;
esac
