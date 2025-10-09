#!/bin/bash
# Script de mise à jour pour /opt/deploy_secure.sh avec avances intelligentes
# Usage: ./update_deploy_secure.sh

echo "🔄 Mise à jour du script de déploiement sécurisé avec avances intelligentes"
echo "=========================================================================="

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./update_deploy_secure.sh"
    exit 1
fi

# Vérifier que le script original existe
if [ ! -f "/opt/deploy_secure.sh" ]; then
    echo "❌ Le script /opt/deploy_secure.sh n'existe pas"
    echo "   Veuillez d'abord installer le script de déploiement sécurisé"
    exit 1
fi

echo "✅ Script original trouvé: /opt/deploy_secure.sh"

# Créer une sauvegarde du script original
echo "📦 Création d'une sauvegarde du script original..."
cp /opt/deploy_secure.sh /opt/deploy_secure.sh.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Sauvegarde créée"

# Fonction pour ajouter les nouvelles fonctionnalités
add_avances_features() {
    echo "🔧 Ajout des fonctionnalités d'avances intelligentes..."
    
    # Créer un script temporaire avec les modifications
    cat > /tmp/deploy_secure_updated.sh << 'EOF'
#!/bin/bash
# Script de déploiement sécurisé avec avances intelligentes
# Version mise à jour avec système d'avances intelligent

# Configuration des avances intelligentes
AVANCES_BRANCH="modifications-octobre-2025"
AVANCES_MIGRATIONS=("paiements.0011_add_manual_month_selection_fields" "paiements.0012_add_paiement_field_to_avance")

# Fonction de sauvegarde des avances
backup_avances_data() {
    echo "📦 Sauvegarde des données d'avances..."
    if [ -f "$PROJECT_DIR/manage.py" ]; then
        cd "$PROJECT_DIR"
        sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py dumpdata paiements.AvanceLoyer paiements.ConsommationAvance > $BACKUP_DIR/backup_avances_$(date +%Y%m%d_%H%M%S).json"
        echo "✅ Données d'avances sauvegardées"
    fi
}

# Fonction de correction des données d'avances
fix_avances_data() {
    echo "🔧 Correction des données d'avances existantes..."
    cd "$PROJECT_DIR"
    
    sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py shell" << 'PYTHON_EOF'
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from datetime import date

print("Début de la correction des données d'avances...")

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

print("Correction des données d'avances terminée")
PYTHON_EOF
    
    echo "✅ Données d'avances corrigées"
}

# Fonction de vérification des avances
verify_avances() {
    echo "🔍 Vérification des avances intelligentes..."
    cd "$PROJECT_DIR"
    
    sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py shell" << 'PYTHON_EOF'
from paiements.models_avance import AvanceLoyer

print("Vérification des avances intelligentes...")

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

print("Vérification des avances terminée")
PYTHON_EOF
    
    echo "✅ Vérification des avances terminée"
}

# Fonction de mise à jour du code avec avances intelligentes
update_code_with_avances() {
    echo "📥 Mise à jour du code avec avances intelligentes..."
    
    cd "$PROJECT_DIR"
    
    if [ -d ".git" ]; then
        # Sauvegarder les modifications locales
        sudo -u $APP_USER git stash push -m "Sauvegarde avant mise à jour avances intelligentes $(date +%Y%m%d_%H%M%S)"
        
        # Récupérer les dernières modifications
        sudo -u $APP_USER git fetch origin
        sudo -u $APP_USER git checkout "$AVANCES_BRANCH"
        sudo -u $APP_USER git pull origin "$AVANCES_BRANCH"
        
        echo "✅ Code mis à jour avec avances intelligentes"
    else
        echo "❌ Pas de repository Git trouvé"
        exit 1
    fi
}

# Fonction d'application des migrations d'avances
apply_avances_migrations() {
    echo "🗄️ Application des migrations d'avances intelligentes..."
    
    cd "$PROJECT_DIR"
    
    # Appliquer les migrations spécifiques aux avances
    for migration in "${AVANCES_MIGRATIONS[@]}"; do
        echo "   Application de la migration: $migration"
        sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py migrate $migration"
    done
    
    echo "✅ Migrations d'avances appliquées"
}

# Fonction de test des avances intelligentes
test_avances_features() {
    echo "🧪 Test des fonctionnalités d'avances intelligentes..."
    
    cd "$PROJECT_DIR"
    
    # Test de création d'avance
    sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py shell" << 'PYTHON_EOF'
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat
from decimal import Decimal
from datetime import date

print("Test des fonctionnalités d'avances intelligentes...")

# Récupérer un contrat
contrat = Contrat.objects.first()
if contrat:
    try:
        # Créer une avance de test
        avance = ServiceGestionAvance.creer_avance_loyer(
            contrat=contrat,
            montant_avance=Decimal('100000'),
            date_avance=date.today(),
            notes="Test avances intelligentes"
        )
        print(f"Avance créée: {avance.id}, Statut: {avance.statut}")
        print(f"Paiement associé: {avance.paiement}")
        
        # Supprimer l'avance de test
        avance.delete()
        print("Test des avances intelligentes réussi")
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        raise
else:
    print("Aucun contrat trouvé pour le test")
PYTHON_EOF
    
    echo "✅ Test des avances intelligentes réussi"
}

# Fonction principale de mise à jour des avances
update_avances_intelligent_system() {
    echo "🚀 Mise à jour du système d'avances intelligentes..."
    
    # Sauvegarder les données d'avances
    backup_avances_data
    
    # Mettre à jour le code
    update_code_with_avances
    
    # Installer les dépendances
    install_dependencies
    
    # Appliquer les migrations
    apply_avances_migrations
    
    # Corriger les données
    fix_avances_data
    
    # Collecter les fichiers statiques
    collect_static_files
    
    # Redémarrer les services
    restart_services
    
    # Vérifier le déploiement
    verify_avances
    
    # Tester les fonctionnalités
    test_avances_features
    
    echo "✅ Système d'avances intelligentes mis à jour avec succès"
}

# Ajouter les nouvelles fonctionnalités au script principal
echo "🔧 Intégration des fonctionnalités d'avances intelligentes..."

# Lire le script original et ajouter les nouvelles fonctions
{
    # Lire le script original jusqu'à la fonction main
    sed '/^main()/,/^}/!d' /opt/deploy_secure.sh | head -n -1
    
    # Ajouter l'appel à la mise à jour des avances
    echo "    # Mise à jour du système d'avances intelligentes"
    echo "    update_avances_intelligent_system"
    echo "}"
    
    # Ajouter toutes les nouvelles fonctions
    cat << 'FUNCTIONS_EOF'

# =====================================================
# FONCTIONS D'AVANCES INTELLIGENTES
# =====================================================

# Configuration des avances intelligentes
AVANCES_BRANCH="modifications-octobre-2025"
AVANCES_MIGRATIONS=("paiements.0011_add_manual_month_selection_fields" "paiements.0012_add_paiement_field_to_avance")

# Fonction de sauvegarde des avances
backup_avances_data() {
    echo "📦 Sauvegarde des données d'avances..."
    if [ -f "$PROJECT_DIR/manage.py" ]; then
        cd "$PROJECT_DIR"
        sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py dumpdata paiements.AvanceLoyer paiements.ConsommationAvance > $BACKUP_DIR/backup_avances_$(date +%Y%m%d_%H%M%S).json"
        echo "✅ Données d'avances sauvegardées"
    fi
}

# Fonction de correction des données d'avances
fix_avances_data() {
    echo "🔧 Correction des données d'avances existantes..."
    cd "$PROJECT_DIR"
    
    sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py shell" << 'PYTHON_EOF'
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from datetime import date

print("Début de la correction des données d'avances...")

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

print("Correction des données d'avances terminée")
PYTHON_EOF
    
    echo "✅ Données d'avances corrigées"
}

# Fonction de vérification des avances
verify_avances() {
    echo "🔍 Vérification des avances intelligentes..."
    cd "$PROJECT_DIR"
    
    sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py shell" << 'PYTHON_EOF'
from paiements.models_avance import AvanceLoyer

print("Vérification des avances intelligentes...")

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

print("Vérification des avances terminée")
PYTHON_EOF
    
    echo "✅ Vérification des avances terminée"
}

# Fonction de mise à jour du code avec avances intelligentes
update_code_with_avances() {
    echo "📥 Mise à jour du code avec avances intelligentes..."
    
    cd "$PROJECT_DIR"
    
    if [ -d ".git" ]; then
        # Sauvegarder les modifications locales
        sudo -u $APP_USER git stash push -m "Sauvegarde avant mise à jour avances intelligentes $(date +%Y%m%d_%H%M%S)"
        
        # Récupérer les dernières modifications
        sudo -u $APP_USER git fetch origin
        sudo -u $APP_USER git checkout "$AVANCES_BRANCH"
        sudo -u $APP_USER git pull origin "$AVANCES_BRANCH"
        
        echo "✅ Code mis à jour avec avances intelligentes"
    else
        echo "❌ Pas de repository Git trouvé"
        exit 1
    fi
}

# Fonction d'application des migrations d'avances
apply_avances_migrations() {
    echo "🗄️ Application des migrations d'avances intelligentes..."
    
    cd "$PROJECT_DIR"
    
    # Appliquer les migrations spécifiques aux avances
    for migration in "${AVANCES_MIGRATIONS[@]}"; do
        echo "   Application de la migration: $migration"
        sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py migrate $migration"
    done
    
    echo "✅ Migrations d'avances appliquées"
}

# Fonction de test des avances intelligentes
test_avances_features() {
    echo "🧪 Test des fonctionnalités d'avances intelligentes..."
    
    cd "$PROJECT_DIR"
    
    # Test de création d'avance
    sudo -u $APP_USER bash -c "source venv/bin/activate && export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS && python manage.py shell" << 'PYTHON_EOF'
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat
from decimal import Decimal
from datetime import date

print("Test des fonctionnalités d'avances intelligentes...")

# Récupérer un contrat
contrat = Contrat.objects.first()
if contrat:
    try:
        # Créer une avance de test
        avance = ServiceGestionAvance.creer_avance_loyer(
            contrat=contrat,
            montant_avance=Decimal('100000'),
            date_avance=date.today(),
            notes="Test avances intelligentes"
        )
        print(f"Avance créée: {avance.id}, Statut: {avance.statut}")
        print(f"Paiement associé: {avance.paiement}")
        
        # Supprimer l'avance de test
        avance.delete()
        print("Test des avances intelligentes réussi")
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        raise
else:
    print("Aucun contrat trouvé pour le test")
PYTHON_EOF
    
    echo "✅ Test des avances intelligentes réussi"
}

# Fonction principale de mise à jour des avances
update_avances_intelligent_system() {
    echo "🚀 Mise à jour du système d'avances intelligentes..."
    
    # Sauvegarder les données d'avances
    backup_avances_data
    
    # Mettre à jour le code
    update_code_with_avances
    
    # Installer les dépendances
    install_dependencies
    
    # Appliquer les migrations
    apply_avances_migrations
    
    # Corriger les données
    fix_avances_data
    
    # Collecter les fichiers statiques
    collect_static_files
    
    # Redémarrer les services
    restart_services
    
    # Vérifier le déploiement
    verify_avances
    
    # Tester les fonctionnalités
    test_avances_features
    
    echo "✅ Système d'avances intelligentes mis à jour avec succès"
}

FUNCTIONS_EOF

} > /tmp/deploy_secure_updated.sh

# Remplacer le script original
echo "🔄 Remplacement du script original..."
mv /tmp/deploy_secure_updated.sh /opt/deploy_secure.sh
chmod +x /opt/deploy_secure.sh

echo "✅ Script /opt/deploy_secure.sh mis à jour avec succès"
echo ""
echo "🎉 Mise à jour terminée !"
echo ""
echo "📋 Nouvelles fonctionnalités ajoutées :"
echo "   - Intégration automatique des avances dans le système de paiement"
echo "   - Détection intelligente des avances existantes"
echo "   - Sélection manuelle des mois couverts"
echo "   - Correction automatique des données existantes"
echo "   - Interface utilisateur améliorée"
echo ""
echo "🚀 Pour déployer :"
echo "   sudo /opt/deploy_secure.sh"
echo ""
echo "📊 Le script gère maintenant automatiquement :"
echo "   - Sauvegarde des données d'avances"
echo "   - Mise à jour vers la branche modifications-octobre-2025"
echo "   - Application des migrations 0011 et 0012"
echo "   - Correction des dates incorrectes (0225 → 2025)"
echo "   - Recalcul des montants restants"
echo "   - Test des nouvelles fonctionnalités"
echo ""
echo "✅ Votre script de déploiement sécurisé est maintenant prêt !"
