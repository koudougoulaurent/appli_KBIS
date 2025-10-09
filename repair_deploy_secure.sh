#!/bin/bash
# Script de réparation pour /opt/deploy_secure.sh
# Usage: ./repair_deploy_secure.sh

echo "🔧 Réparation du script /opt/deploy_secure.sh"
echo "============================================="

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./repair_deploy_secure.sh"
    exit 1
fi

# Configuration pour kbis_immobilier
APP_NAME="kbis_immobilier"
PROJECT_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="gestimmob"
BACKUP_DIR="/var/backups/kbis_immobilier"
AVANCES_BRANCH="modifications-octobre-2025"

echo "✅ Configuration détectée :"
echo "   - Application: $APP_NAME"
echo "   - Répertoire: $PROJECT_DIR"
echo "   - Service: $SERVICE_NAME"
echo "   - Sauvegarde: $BACKUP_DIR"

# Créer une sauvegarde du script cassé
echo "📦 Création d'une sauvegarde du script cassé..."
cp /opt/deploy_secure.sh /opt/deploy_secure.sh.broken.$(date +%Y%m%d_%H%M%S)
echo "✅ Sauvegarde créée"

# Créer le répertoire de sauvegarde s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# Reconstruire le script correctement
echo "🔧 Reconstruction du script /opt/deploy_secure.sh..."

cat > /opt/deploy_secure.sh << 'EOF'
#!/bin/bash
# Script de déploiement sécurisé avec avances intelligentes
# Version réparée pour kbis_immobilier

# Configuration spécifique à kbis_immobilier
APP_NAME="kbis_immobilier"
PROJECT_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="gestimmob"
BACKUP_DIR="/var/backups/kbis_immobilier"
AVANCES_BRANCH="modifications-octobre-2025"
AVANCES_MIGRATIONS=("paiements.0011_add_manual_month_selection_fields" "paiements.0012_add_paiement_field_to_avance")

# Fonction de sauvegarde des avances
backup_avances_data() {
    echo "📦 Sauvegarde des données d'avances pour kbis_immobilier..."
    if [ -f "$PROJECT_DIR/manage.py" ]; then
        cd "$PROJECT_DIR"
        # Déterminer l'utilisateur approprié
        if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
            # Utiliser l'environnement virtuel
            source venv/bin/activate
            python manage.py dumpdata paiements.AvanceLoyer paiements.ConsommationAvance > $BACKUP_DIR/backup_avances_$(date +%Y%m%d_%H%M%S).json
        else
            # Utiliser python3 directement
            python3 manage.py dumpdata paiements.AvanceLoyer paiements.ConsommationAvance > $BACKUP_DIR/backup_avances_$(date +%Y%m%d_%H%M%S).json
        fi
        echo "✅ Données d'avances sauvegardées"
    else
        echo "⚠️  Fichier manage.py non trouvé dans $PROJECT_DIR"
    fi
}

# Fonction de correction des données d'avances
fix_avances_data() {
    echo "🔧 Correction des données d'avances existantes pour kbis_immobilier..."
    cd "$PROJECT_DIR"
    
    # Script de correction des données
    cat > /tmp/fix_avances.py << 'PYTHON_EOF'
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append('/var/www/kbis_immobilier')
django.setup()

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
    
    # Exécuter le script de correction
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source venv/bin/activate
        python /tmp/fix_avances.py
    else
        python3 /tmp/fix_avances.py
    fi
    
    # Nettoyer le script temporaire
    rm -f /tmp/fix_avances.py
    
    echo "✅ Données d'avances corrigées"
}

# Fonction de vérification des avances
verify_avances() {
    echo "🔍 Vérification des avances intelligentes pour kbis_immobilier..."
    cd "$PROJECT_DIR"
    
    # Script de vérification
    cat > /tmp/verify_avances.py << 'PYTHON_EOF'
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append('/var/www/kbis_immobilier')
django.setup()

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
    
    # Exécuter le script de vérification
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source venv/bin/activate
        python /tmp/verify_avances.py
    else
        python3 /tmp/verify_avances.py
    fi
    
    # Nettoyer le script temporaire
    rm -f /tmp/verify_avances.py
    
    echo "✅ Vérification des avances terminée"
}

# Fonction de mise à jour du code avec avances intelligentes
update_code_with_avances() {
    echo "📥 Mise à jour du code avec avances intelligentes pour kbis_immobilier..."
    
    cd "$PROJECT_DIR"
    
    if [ -d ".git" ]; then
        # Sauvegarder les modifications locales
        git stash push -m "Sauvegarde avant mise à jour avances intelligentes $(date +%Y%m%d_%H%M%S)"
        
        # Récupérer les dernières modifications
        git fetch origin
        git checkout "$AVANCES_BRANCH"
        git pull origin "$AVANCES_BRANCH"
        
        echo "✅ Code mis à jour avec avances intelligentes"
    else
        echo "❌ Pas de repository Git trouvé dans $PROJECT_DIR"
        exit 1
    fi
}

# Fonction d'application des migrations d'avances
apply_avances_migrations() {
    echo "🗄️ Application des migrations d'avances intelligentes pour kbis_immobilier..."
    
    cd "$PROJECT_DIR"
    
    # Appliquer les migrations spécifiques aux avances
    for migration in "${AVANCES_MIGRATIONS[@]}"; do
        echo "   Application de la migration: $migration"
        if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
            source venv/bin/activate
            python manage.py migrate $migration
        else
            python3 manage.py migrate $migration
        fi
    done
    
    echo "✅ Migrations d'avances appliquées"
}

# Fonction de test des avances intelligentes
test_avances_features() {
    echo "🧪 Test des fonctionnalités d'avances intelligentes pour kbis_immobilier..."
    
    cd "$PROJECT_DIR"
    
    # Script de test
    cat > /tmp/test_avances.py << 'PYTHON_EOF'
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append('/var/www/kbis_immobilier')
django.setup()

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
    
    # Exécuter le script de test
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source venv/bin/activate
        python /tmp/test_avances.py
    else
        python3 /tmp/test_avances.py
    fi
    
    # Nettoyer le script temporaire
    rm -f /tmp/test_avances.py
    
    echo "✅ Test des avances intelligentes réussi"
}

# Fonction principale de mise à jour des avances
update_avances_intelligent_system() {
    echo "🚀 Mise à jour du système d'avances intelligentes pour kbis_immobilier..."
    
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
    
    echo "✅ Système d'avances intelligentes mis à jour avec succès pour kbis_immobilier"
}

# Fonction main (à adapter selon votre script original)
main() {
    echo "🚀 Déploiement de kbis_immobilier avec avances intelligentes"
    echo "=========================================================="
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -f "$PROJECT_DIR/manage.py" ]; then
        echo "❌ Répertoire de projet incorrect: $PROJECT_DIR"
        exit 1
    fi
    
    # Exécuter les étapes de déploiement
    update_avances_intelligent_system
    
    echo "✅ Déploiement terminé avec succès !"
}

# Exécuter le script principal
main "$@"
EOF

# Rendre le script exécutable
chmod +x /opt/deploy_secure.sh

echo "✅ Script /opt/deploy_secure.sh reconstruit avec succès"

# Vérifier la syntaxe
echo "🔍 Vérification de la syntaxe..."
if bash -n /opt/deploy_secure.sh; then
    echo "✅ Syntaxe du script corrigée"
else
    echo "❌ Le script a encore des erreurs de syntaxe"
    echo "   Veuillez vérifier manuellement"
    exit 1
fi

echo ""
echo "🎉 Réparation terminée !"
echo ""
echo "📋 Configuration appliquée :"
echo "   - Application: $APP_NAME"
echo "   - Répertoire: $PROJECT_DIR"
echo "   - Service: $SERVICE_NAME"
echo "   - Sauvegarde: $BACKUP_DIR"
echo ""
echo "🚀 Vous pouvez maintenant utiliser :"
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
echo "✅ Votre script de déploiement sécurisé est maintenant réparé !"
