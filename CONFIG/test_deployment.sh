#!/bin/bash

# Script de test pour vérifier le déploiement KBIS Immobilier
# À exécuter après le déploiement pour valider l'installation

set -e

# Variables
APP_NAME="kbis-immobilier"
SERVICE_NAME="kbis-immobilier"
APP_DIR="/home/kbis/appli_KBIS"

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

# Test de la connectivité réseau
test_network() {
    log_info "Test de la connectivité réseau..."
    
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_success "Connectivité Internet OK"
    else
        log_error "Pas de connectivité Internet"
        return 1
    fi
}

# Test des services système
test_services() {
    log_info "Test des services système..."
    
    # Test PostgreSQL
    if sudo systemctl is-active --quiet postgresql; then
        log_success "PostgreSQL est actif"
    else
        log_error "PostgreSQL n'est pas actif"
        return 1
    fi
    
    # Test Nginx
    if sudo systemctl is-active --quiet nginx; then
        log_success "Nginx est actif"
    else
        log_error "Nginx n'est pas actif"
        return 1
    fi
    
    # Test de l'application Django
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log_success "Application Django est active"
    else
        log_error "Application Django n'est pas active"
        return 1
    fi
}

# Test de la base de données
test_database() {
    log_info "Test de la base de données..."
    
    cd $APP_DIR
    source venv/bin/activate
    
    # Test de connexion à la base de données
    if python manage.py dbshell -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Connexion à la base de données OK"
    else
        log_error "Erreur de connexion à la base de données"
        return 1
    fi
    
    # Test des migrations
    if python manage.py showmigrations --plan | grep -q "\[ \]"; then
        log_warning "Des migrations en attente détectées"
    else
        log_success "Toutes les migrations sont appliquées"
    fi
}

# Test de l'application web
test_web_app() {
    log_info "Test de l'application web..."
    
    # Test de la page d'accueil
    if curl -f -s http://localhost > /dev/null; then
        log_success "Page d'accueil accessible"
    else
        log_error "Page d'accueil non accessible"
        return 1
    fi
    
    # Test de la page d'administration
    if curl -f -s http://localhost/admin > /dev/null; then
        log_success "Page d'administration accessible"
    else
        log_warning "Page d'administration non accessible"
    fi
    
    # Test des fichiers statiques
    if curl -f -s http://localhost/static/admin/css/base.css > /dev/null; then
        log_success "Fichiers statiques servis correctement"
    else
        log_warning "Problème avec les fichiers statiques"
    fi
}

# Test des performances
test_performance() {
    log_info "Test des performances..."
    
    # Test de charge simple
    if command -v ab > /dev/null 2>&1; then
        log_info "Test de charge avec Apache Bench..."
        if ab -n 100 -c 10 http://localhost/ > /dev/null 2>&1; then
            log_success "Test de charge réussi"
        else
            log_warning "Test de charge échoué"
        fi
    else
        log_warning "Apache Bench non installé, test de charge ignoré"
    fi
    
    # Vérification de l'utilisation mémoire
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log_info "Utilisation mémoire: ${MEMORY_USAGE}%"
    
    if (( $(echo "$MEMORY_USAGE < 80" | bc -l) )); then
        log_success "Utilisation mémoire acceptable"
    else
        log_warning "Utilisation mémoire élevée"
    fi
}

# Test de sécurité
test_security() {
    log_info "Test de sécurité..."
    
    # Vérification des ports ouverts
    OPEN_PORTS=$(sudo netstat -tlnp | grep -E ':(80|443|22|5432)' | wc -l)
    log_info "Ports ouverts détectés: $OPEN_PORTS"
    
    # Vérification du pare-feu
    if command -v ufw > /dev/null 2>&1; then
        if sudo ufw status | grep -q "Status: active"; then
            log_success "Pare-feu UFW actif"
        else
            log_warning "Pare-feu UFW non actif"
        fi
    fi
    
    # Vérification des permissions
    if [ -w "$APP_DIR" ]; then
        log_success "Permissions d'écriture OK"
    else
        log_error "Problème de permissions d'écriture"
        return 1
    fi
}

# Test des logs
test_logs() {
    log_info "Test des logs..."
    
    # Vérification des logs de l'application
    if [ -f "/var/log/gunicorn/kbis_error.log" ]; then
        ERROR_COUNT=$(grep -c "ERROR" /var/log/gunicorn/kbis_error.log 2>/dev/null || echo "0")
        if [ "$ERROR_COUNT" -eq 0 ]; then
            log_success "Aucune erreur dans les logs Gunicorn"
        else
            log_warning "$ERROR_COUNT erreurs dans les logs Gunicorn"
        fi
    fi
    
    # Vérification des logs Nginx
    if [ -f "/var/log/nginx/kbis_error.log" ]; then
        ERROR_COUNT=$(grep -c "error" /var/log/nginx/kbis_error.log 2>/dev/null || echo "0")
        if [ "$ERROR_COUNT" -eq 0 ]; then
            log_success "Aucune erreur dans les logs Nginx"
        else
            log_warning "$ERROR_COUNT erreurs dans les logs Nginx"
        fi
    fi
}

# Test de la configuration SSL (si applicable)
test_ssl() {
    log_info "Test de la configuration SSL..."
    
    if curl -f -s https://localhost > /dev/null 2>&1; then
        log_success "HTTPS fonctionne"
        
        # Test de la redirection HTTP vers HTTPS
        if curl -s -I http://localhost | grep -q "301\|302"; then
            log_success "Redirection HTTP vers HTTPS active"
        else
            log_warning "Pas de redirection HTTP vers HTTPS"
        fi
    else
        log_info "HTTPS non configuré (normal si pas de certificat SSL)"
    fi
}

# Rapport final
generate_report() {
    log_info "Génération du rapport de test..."
    
    echo ""
    echo "=========================================="
    echo "RAPPORT DE TEST - KBIS IMMOBILIER"
    echo "=========================================="
    echo "Date: $(date)"
    echo "Serveur: $(hostname)"
    echo "IP: $(curl -s ifconfig.me 2>/dev/null || echo 'N/A')"
    echo ""
    
    # Statut des services
    echo "=== SERVICES ==="
    sudo systemctl is-active postgresql nginx $SERVICE_NAME | while read service status; do
        echo "$service: $status"
    done
    echo ""
    
    # Utilisation des ressources
    echo "=== RESSOURCES ==="
    echo "Mémoire:"
    free -h
    echo ""
    echo "Disque:"
    df -h | grep -E "(/$|/home)"
    echo ""
    
    # URLs d'accès
    echo "=== ACCÈS ==="
    echo "HTTP: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')"
    echo "HTTPS: https://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')"
    echo "Admin: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost')/admin"
    echo ""
    
    echo "=========================================="
}

# Fonction principale
main() {
    log_info "Début des tests de déploiement..."
    
    local tests_passed=0
    local tests_total=0
    
    # Liste des tests à exécuter
    tests=(
        "test_network"
        "test_services"
        "test_database"
        "test_web_app"
        "test_performance"
        "test_security"
        "test_logs"
        "test_ssl"
    )
    
    # Exécution des tests
    for test in "${tests[@]}"; do
        tests_total=$((tests_total + 1))
        if $test; then
            tests_passed=$((tests_passed + 1))
        fi
        echo ""
    done
    
    # Génération du rapport
    generate_report
    
    # Résumé final
    echo ""
    if [ $tests_passed -eq $tests_total ]; then
        log_success "Tous les tests sont passés ($tests_passed/$tests_total) !"
        log_success "L'application est prête à être utilisée."
    else
        log_warning "Certains tests ont échoué ($tests_passed/$tests_total)"
        log_info "Consultez les logs pour plus de détails."
    fi
    
    echo ""
    log_info "Pour surveiller l'application en temps réel:"
    log_info "  ./maintenance_vps.sh logs"
    log_info "  ./maintenance_vps.sh status"
}

# Exécution du script
main "$@"
