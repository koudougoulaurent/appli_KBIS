#!/bin/bash

# =====================================================
# SCRIPT DE DÉPLOIEMENT - SYSTÈME AVANCES INTELLIGENTES
# =====================================================
# Date: 09/10/2025
# Version: 2.0
# Description: Déploiement automatisé des avances intelligentes
# =====================================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_DIR="/var/www/appli_KBIS"
BACKUP_DIR="/var/backups/appli_KBIS"
LOG_FILE="/var/log/appli_KBIS/deploy.log"

# Créer le répertoire de logs s'il n'existe pas
mkdir -p "$(dirname "$LOG_FILE")"

# Fonction de logging
log_to_file() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Fonction de sauvegarde
backup_database() {
    log "Création de la sauvegarde de la base de données..."
    
    # Créer le répertoire de sauvegarde s'il n'existe pas
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder la base de données
    cd "$PROJECT_DIR"
    python manage.py dumpdata > "$BACKUP_DIR/backup_avant_avances_intelligentes_$(date +%Y%m%d_%H%M%S).json"
    
    if [ $? -eq 0 ]; then
        success "Sauvegarde créée avec succès"
        log_to_file "Sauvegarde créée: backup_avant_avances_intelligentes_$(date +%Y%m%d_%H%M%S).json"
    else
        error "Échec de la sauvegarde"
        exit 1
    fi
}

# Fonction de mise à jour du code
update_code() {
    log "Mise à jour du code source..."
    
    cd "$PROJECT_DIR"
    
    # Sauvegarder les modifications locales
    git stash push -m "Sauvegarde avant déploiement avances intelligentes $(date +%Y%m%d_%H%M%S)"
    
    # Récupérer les dernières modifications
    git fetch origin
    git checkout modifications-octobre-2025
    git pull origin modifications-octobre-2025
    
    if [ $? -eq 0 ]; then
        success "Code mis à jour avec succès"
        log_to_file "Code mis à jour depuis modifications-octobre-2025"
    else
        error "Échec de la mise à jour du code"
        exit 1
    fi
}

# Fonction d'installation des dépendances
install_dependencies() {
    log "Installation des dépendances..."
    
    cd "$PROJECT_DIR"
    
    # Activer l'environnement virtuel s'il existe
    if [ -d "venv" ]; then
        source venv/bin/activate
        log "Environnement virtuel activé"
    fi
    
    # Installer les dépendances
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        success "Dépendances installées avec succès"
        log_to_file "Dépendances installées"
    else
        error "Échec de l'installation des dépendances"
        exit 1
    fi
}

# Fonction d'application des migrations
apply_migrations() {
    log "Application des migrations..."
    
    cd "$PROJECT_DIR"
    
    # Vérifier l'état des migrations
    log "État des migrations avant application:"
    python manage.py showmigrations paiements
    
    # Appliquer les migrations dans l'ordre
    log "Application de la migration 0011..."
    python manage.py migrate paiements 0011
    
    log "Application de la migration 0012..."
    python manage.py migrate paiements 0012
    
    # Vérifier l'état des migrations après application
    log "État des migrations après application:"
    python manage.py showmigrations paiements
    
    if [ $? -eq 0 ]; then
        success "Migrations appliquées avec succès"
        log_to_file "Migrations 0011 et 0012 appliquées"
    else
        error "Échec de l'application des migrations"
        exit 1
    fi
}

# Fonction de correction des données
fix_data() {
    log "Correction des données existantes..."
    
    cd "$PROJECT_DIR"
    
    # Script de correction des données
    python manage.py shell << 'EOF'
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from datetime import date

print("Début de la correction des données...")

# Corriger les avances avec des dates incorrectes
avances_corrigees = 0
for avance in AvanceLoyer.objects.all():
    corrected = False
    if avance.mois_debut_couverture and avance.mois_debut_couverture.year < 2000:
        avance.mois_debut_couverture = avance.mois_debut_couverture.replace(year=avance.mois_debut_couverture.year + 2000)
        corrected = True
    if avance.mois_fin_couverture and avance.mois_fin_couverture.year < 2000:
        avance.mois_fin_couverture = avance.mois_fin_couverture.replace(year=avance.mois_fin_couverture.year + 2000)
        corrected = True
    if corrected:
        avance.save()
        avances_corrigees += 1

print(f"Avances corrigées: {avances_corrigees}")

# Supprimer les consommations avec des dates incorrectes
consommations_supprimees = ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).count()
ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).delete()

print(f"Consommations supprimées: {consommations_supprimees}")

# Recalculer les montants restants
for avance in AvanceLoyer.objects.all():
    avance.montant_restant = avance.montant_avance
    avance.statut = 'active'
    avance.save()

print("Correction des données terminée")
EOF
    
    if [ $? -eq 0 ]; then
        success "Données corrigées avec succès"
        log_to_file "Données corrigées"
    else
        error "Échec de la correction des données"
        exit 1
    fi
}

# Fonction de vérification
verify_deployment() {
    log "Vérification du déploiement..."
    
    cd "$PROJECT_DIR"
    
    # Vérifier l'intégrité des données
    python manage.py shell << 'EOF'
from paiements.models_avance import AvanceLoyer

print("Vérification de l'intégrité des données...")

# Vérifier les avances
avances = AvanceLoyer.objects.all()
print(f"Total avances: {avances.count()}")

# Vérifier les avances avec des problèmes
problemes = avances.filter(montant_restant__lt=0)
print(f"Avances avec montant restant négatif: {problemes.count()}")

# Vérifier les dates
dates_incorrectes = avances.filter(mois_debut_couverture__year__lt=2000)
print(f"Avances avec dates incorrectes: {dates_incorrectes.count()}")

# Vérifier les nouveaux champs
champs_manquants = avances.filter(paiement__isnull=True).count()
print(f"Avances sans paiement associé: {champs_manquants}")

print("Vérification terminée")
EOF
    
    if [ $? -eq 0 ]; then
        success "Vérification réussie"
        log_to_file "Vérification réussie"
    else
        error "Échec de la vérification"
        exit 1
    fi
}

# Fonction de test
test_functionality() {
    log "Test des nouvelles fonctionnalités..."
    
    cd "$PROJECT_DIR"
    
    # Test de création d'avance
    python manage.py shell << 'EOF'
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat
from decimal import Decimal
from datetime import date

print("Test de création d'avance...")

# Récupérer un contrat
contrat = Contrat.objects.first()
if contrat:
    try:
        # Créer une avance de test
        avance = ServiceGestionAvance.creer_avance_loyer(
            contrat=contrat,
            montant_avance=Decimal('100000'),
            date_avance=date.today(),
            notes="Test déploiement"
        )
        print(f"Avance créée: {avance.id}, Statut: {avance.statut}")
        print(f"Paiement associé: {avance.paiement}")
        
        # Supprimer l'avance de test
        avance.delete()
        print("Test terminé avec succès")
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        raise
else:
    print("Aucun contrat trouvé pour le test")
    raise Exception("Aucun contrat disponible pour le test")
EOF
    
    if [ $? -eq 0 ]; then
        success "Test des fonctionnalités réussi"
        log_to_file "Test des fonctionnalités réussi"
    else
        error "Échec du test des fonctionnalités"
        exit 1
    fi
}

# Fonction de redémarrage des services
restart_services() {
    log "Redémarrage des services..."
    
    # Redémarrer Gunicorn
    if systemctl is-active --quiet gunicorn; then
        sudo systemctl restart gunicorn
        success "Gunicorn redémarré"
    fi
    
    # Redémarrer Nginx
    if systemctl is-active --quiet nginx; then
        sudo systemctl restart nginx
        success "Nginx redémarré"
    fi
    
    # Nettoyer le cache Django
    cd "$PROJECT_DIR"
    python manage.py clear_cache
    
    log_to_file "Services redémarrés"
}

# Fonction principale
main() {
    log "=== DÉBUT DU DÉPLOIEMENT DES AVANCES INTELLIGENTES ==="
    log_to_file "=== DÉBUT DU DÉPLOIEMENT ==="
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -f "$PROJECT_DIR/manage.py" ]; then
        error "Répertoire de projet incorrect: $PROJECT_DIR"
        exit 1
    fi
    
    # Exécuter les étapes de déploiement
    backup_database
    update_code
    install_dependencies
    apply_migrations
    fix_data
    verify_deployment
    test_functionality
    restart_services
    
    success "=== DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ==="
    log_to_file "=== DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ==="
    
    # Afficher les informations de post-déploiement
    echo ""
    echo "🎉 DÉPLOIEMENT RÉUSSI !"
    echo ""
    echo "📋 Informations importantes:"
    echo "   - Sauvegarde: $BACKUP_DIR"
    echo "   - Logs: $LOG_FILE"
    echo "   - Projet: $PROJECT_DIR"
    echo ""
    echo "🔧 Prochaines étapes:"
    echo "   1. Vérifier l'application dans le navigateur"
    echo "   2. Tester la création d'avances"
    echo "   3. Surveiller les logs pour détecter d'éventuels problèmes"
    echo ""
    echo "📞 En cas de problème:"
    echo "   - Consulter les logs: tail -f $LOG_FILE"
    echo "   - Restaurer la sauvegarde si nécessaire"
    echo ""
}

# Exécuter le script principal
main "$@"
