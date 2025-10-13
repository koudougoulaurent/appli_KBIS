#!/bin/bash

# ===========================================
# MONITEUR DE SANTÉ KBIS IMMOBILIER
# ===========================================
# Ce script vérifie la santé du service après déploiement
# Usage: ./health_monitor.sh [options]

set -e

# Configuration
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis-immobilier"
DB_FILE="$APP_DIR/db.sqlite3"
LOG_FILE="/var/log/kbis_health.log"
ALERT_EMAIL="admin@kbis.bf"  # À configurer selon vos besoins

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

# Vérifier le statut des services système
check_system_services() {
    log "🔍 Vérification des services système..."
    local all_good=true
    
    # Vérifier Nginx
    if systemctl is-active --quiet nginx; then
        log_success "Nginx est actif"
    else
        log_error "Nginx n'est pas actif"
        all_good=false
    fi
    
    # Vérifier le service Django
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Service $SERVICE_NAME est actif"
    else
        log_error "Service $SERVICE_NAME n'est pas actif"
        all_good=false
    fi
    
    # Vérifier les ports
    if netstat -tlnp | grep -q ":80 "; then
        log_success "Port 80 est ouvert"
    else
        log_error "Port 80 n'est pas ouvert"
        all_good=false
    fi
    
    if netstat -tlnp | grep -q ":8000 "; then
        log_success "Port 8000 est ouvert"
    else
        log_error "Port 8000 n'est pas ouvert"
        all_good=false
    fi
    
    if [ "$all_good" = true ]; then
        return 0
    else
        return 1
    fi
}

# Vérifier la base de données
check_database() {
    log "🗄️  Vérification de la base de données..."
    
    if [ ! -f "$DB_FILE" ]; then
        log_error "Fichier de base de données non trouvé: $DB_FILE"
        return 1
    fi
    
    # Vérifier les permissions
    if [ ! -r "$DB_FILE" ] || [ ! -w "$DB_FILE" ]; then
        log_error "Permissions insuffisantes sur la base de données"
        return 1
    fi
    
    # Vérifier l'intégrité de la base
    if sqlite3 "$DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
        log_success "Intégrité de la base de données OK"
    else
        log_error "Problème d'intégrité de la base de données"
        return 1
    fi
    
    # Vérifier les tables critiques
    local critical_tables=(
        "django_migrations"
        "utilisateurs_utilisateur"
        "core_configurationentreprise"
    )
    
    for table in "${critical_tables[@]}"; do
        if sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';" | grep -q "$table"; then
            log_success "Table $table existe"
        else
            log_error "Table critique manquante: $table"
            return 1
        fi
    done
    
    return 0
}

# Vérifier la connectivité HTTP
check_http_connectivity() {
    log "🌐 Vérification de la connectivité HTTP..."
    local max_attempts=10
    local attempt=1
    local success=false
    
    while [ $attempt -le $max_attempts ]; do
        log "Tentative $attempt/$max_attempts..."
        
        # Test de connectivité de base
        if curl -s -f -m 10 http://localhost:8000/ > /dev/null 2>&1; then
            log_success "Service accessible via HTTP (localhost:8000)"
            success=true
            break
        else
            log_warning "Échec tentative $attempt - Attente 3s..."
            sleep 3
            ((attempt++))
        fi
    done
    
    if [ "$success" = false ]; then
        log_error "Service non accessible après $max_attempts tentatives"
        return 1
    fi
    
    # Test via Nginx
    if curl -s -f -m 10 http://localhost/ > /dev/null 2>&1; then
        log_success "Service accessible via Nginx (localhost)"
    else
        log_warning "Service non accessible via Nginx"
        return 1
    fi
    
    return 0
}

# Vérifier les endpoints critiques
check_critical_endpoints() {
    log "🎯 Vérification des endpoints critiques..."
    local endpoints=(
        "/"
        "/utilisateurs/connexion-groupes/"
        "/admin/"
    )
    
    local all_good=true
    
    for endpoint in "${endpoints[@]}"; do
        local url="http://localhost:8000$endpoint"
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$url" 2>/dev/null || echo "000")
        
        case $status_code in
            200|301|302)
                log_success "Endpoint $endpoint répond correctement ($status_code)"
                ;;
            403)
                log_warning "Endpoint $endpoint retourne 403 (peut être normal)"
                ;;
            404)
                log_warning "Endpoint $endpoint non trouvé (404)"
                ;;
            500)
                log_error "Endpoint $endpoint retourne une erreur serveur (500)"
                all_good=false
                ;;
            *)
                log_error "Endpoint $endpoint non accessible (code: $status_code)"
                all_good=false
                ;;
        esac
    done
    
    if [ "$all_good" = true ]; then
        return 0
    else
        return 1
    fi
}

# Vérifier les ressources système
check_system_resources() {
    log "💻 Vérification des ressources système..."
    
    # Vérifier l'espace disque
    local disk_usage=$(df "$APP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 90 ]; then
        log_success "Espace disque OK ($disk_usage% utilisé)"
    else
        log_warning "Espace disque faible ($disk_usage% utilisé)"
    fi
    
    # Vérifier la mémoire
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$memory_usage" -lt 90 ]; then
        log_success "Mémoire OK ($memory_usage% utilisée)"
    else
        log_warning "Mémoire élevée ($memory_usage% utilisée)"
    fi
    
    # Vérifier les processus
    local gunicorn_processes=$(pgrep -f gunicorn | wc -l)
    if [ "$gunicorn_processes" -gt 0 ]; then
        log_success "Processus Gunicorn actifs ($gunicorn_processes)"
    else
        log_error "Aucun processus Gunicorn actif"
        return 1
    fi
    
    return 0
}

# Vérifier les logs d'erreur
check_error_logs() {
    log "📋 Vérification des logs d'erreur..."
    
    # Vérifier les logs du service
    local recent_errors=$(journalctl -u "$SERVICE_NAME" --since "5 minutes ago" --no-pager | grep -i error | wc -l)
    if [ "$recent_errors" -eq 0 ]; then
        log_success "Aucune erreur récente dans les logs du service"
    else
        log_warning "$recent_errors erreur(s) récente(s) dans les logs du service"
        journalctl -u "$SERVICE_NAME" --since "5 minutes ago" --no-pager | grep -i error | tail -5
    fi
    
    # Vérifier les logs Nginx
    local nginx_errors=$(tail -100 /var/log/nginx/error.log 2>/dev/null | grep -i error | wc -l)
    if [ "$nginx_errors" -eq 0 ]; then
        log_success "Aucune erreur récente dans les logs Nginx"
    else
        log_warning "$nginx_errors erreur(s) récente(s) dans les logs Nginx"
    fi
    
    return 0
}

# Test de performance
check_performance() {
    log "⚡ Test de performance..."
    
    # Test de temps de réponse
    local response_time=$(curl -s -o /dev/null -w "%{time_total}" -m 10 http://localhost:8000/ 2>/dev/null || echo "999")
    local response_time_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "999")
    
    if (( $(echo "$response_time < 2.0" | bc -l) )); then
        log_success "Temps de réponse acceptable (${response_time_ms}ms)"
    else
        log_warning "Temps de réponse élevé (${response_time_ms}ms)"
    fi
    
    # Test de charge
    local concurrent_requests=5
    local success_count=0
    
    for i in $(seq 1 $concurrent_requests); do
        if curl -s -f -m 5 http://localhost:8000/ > /dev/null 2>&1; then
            ((success_count++))
        fi
    done
    
    local success_rate=$((success_count * 100 / concurrent_requests))
    if [ "$success_rate" -ge 80 ]; then
        log_success "Taux de succès acceptable ($success_rate%)"
    else
        log_warning "Taux de succès faible ($success_rate%)"
    fi
    
    return 0
}

# Générer un rapport de santé
generate_health_report() {
    local report_file="/tmp/kbis_health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log "📊 Génération du rapport de santé: $report_file"
    
    cat > "$report_file" << EOF
===========================================
RAPPORT DE SANTÉ KBIS IMMOBILIER
===========================================
Date: $(date)
Hostname: $(hostname)
Uptime: $(uptime)

=== SERVICES SYSTÈME ===
Nginx: $(systemctl is-active nginx)
Service Django: $(systemctl is-active $SERVICE_NAME)

=== CONNECTIVITÉ ===
Port 80: $(netstat -tlnp | grep ":80 " | wc -l) processus
Port 8000: $(netstat -tlnp | grep ":8000 " | wc -l) processus

=== BASE DE DONNÉES ===
Fichier: $DB_FILE
Taille: $(du -h "$DB_FILE" 2>/dev/null | cut -f1 || echo "N/A")
Permissions: $(ls -l "$DB_FILE" 2>/dev/null | awk '{print $1}' || echo "N/A")

=== RESSOURCES SYSTÈME ===
Espace disque: $(df -h "$APP_DIR" | awk 'NR==2 {print $5}')
Mémoire: $(free -h | awk 'NR==2 {print $3 "/" $2}')
Processus Gunicorn: $(pgrep -f gunicorn | wc -l)

=== PERFORMANCE ===
Temps de réponse: $(curl -s -o /dev/null -w "%{time_total}s" http://localhost:8000/ 2>/dev/null || echo "N/A")

=== LOGS RÉCENTS ===
$(journalctl -u "$SERVICE_NAME" --since "10 minutes ago" --no-pager | tail -10)

===========================================
EOF
    
    echo "$report_file"
}

# Fonction principale
main() {
    local mode=${1:-"full"}
    local report_file=""
    
    log "🏥 Début de la vérification de santé - Mode: $mode"
    
    # Créer le répertoire de logs
    mkdir -p "$(dirname "$LOG_FILE")"
    
    local overall_status=0
    
    case "$mode" in
        "full")
            check_system_services || overall_status=1
            check_database || overall_status=1
            check_http_connectivity || overall_status=1
            check_critical_endpoints || overall_status=1
            check_system_resources || overall_status=1
            check_error_logs
            check_performance
            report_file=$(generate_health_report)
            ;;
        "quick")
            check_system_services || overall_status=1
            check_http_connectivity || overall_status=1
            ;;
        "database")
            check_database || overall_status=1
            ;;
        "services")
            check_system_services || overall_status=1
            ;;
        "performance")
            check_performance
            ;;
        *)
            echo "Usage: $0 [full|quick|database|services|performance]"
            echo
            echo "Modes de vérification:"
            echo "  full        - Vérification complète (défaut)"
            echo "  quick       - Vérification rapide (services + HTTP)"
            echo "  database    - Vérification de la base de données uniquement"
            echo "  services    - Vérification des services uniquement"
            echo "  performance - Test de performance uniquement"
            exit 1
            ;;
    esac
    
    if [ "$overall_status" -eq 0 ]; then
        log_success "Vérification de santé terminée - Tous les tests sont passés"
        if [ -n "$report_file" ]; then
            log "Rapport généré: $report_file"
        fi
    else
        log_error "Vérification de santé terminée - Des problèmes ont été détectés"
        if [ -n "$report_file" ]; then
            log "Rapport généré: $report_file"
        fi
        exit 1
    fi
}

# Exécution
main "$@"
