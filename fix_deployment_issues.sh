#!/bin/bash
# Script de correction des problèmes de déploiement
# Usage: ./fix_deployment_issues.sh

echo "🔧 Correction des problèmes de déploiement"
echo "=========================================="

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./fix_deployment_issues.sh"
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

# 1. Nettoyer les fichiers en conflit
echo "🧹 Nettoyage des fichiers en conflit..."
cd "$PROJECT_DIR"

# Supprimer les fichiers en conflit
rm -f fix_broken_file.sh
rm -f fix_emergency_vps.sh
rm -f fix_imports_direct.sh
rm -f fix_imports_final_vps.sh
rm -f fix_imports_simple.sh
rm -f fix_imports_vps.sh
rm -f fix_models_missing.sh
rm -f fix_vps_final.sh
rm -f fix_vps_improved_design.sh

echo "✅ Fichiers en conflit supprimés"

# 2. Forcer la mise à jour Git
echo "📥 Mise à jour forcée du code..."
cd "$PROJECT_DIR"

# Sauvegarder les modifications locales
git stash push -m "Sauvegarde avant correction $(date +%Y%m%d_%H%M%S)"

# Forcer la mise à jour
git fetch origin
git reset --hard origin/$AVANCES_BRANCH

echo "✅ Code mis à jour"

# 3. Installer les dépendances
echo "📦 Installation des dépendances..."
cd "$PROJECT_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Dépendances installées via venv"
else
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    echo "✅ Dépendances installées via pip3"
fi

# 4. Appliquer les migrations correctement
echo "🗄️ Application des migrations..."
cd "$PROJECT_DIR"

# Appliquer toutes les migrations
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py migrate
else
    python3 manage.py migrate
fi

echo "✅ Migrations appliquées"

# 5. Corriger les données d'avances
echo "🔧 Correction des données d'avances..."
cd "$PROJECT_DIR"

# Script de correction des données
cat > /tmp/fix_avances_corrected.py << 'PYTHON_EOF'
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
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python /tmp/fix_avances_corrected.py
else
    python3 /tmp/fix_avances_corrected.py
fi

# Nettoyer le script temporaire
rm -f /tmp/fix_avances_corrected.py

echo "✅ Données d'avances corrigées"

# 6. Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
cd "$PROJECT_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py collectstatic --noinput
else
    python3 manage.py collectstatic --noinput
fi

echo "✅ Fichiers statiques collectés"

# 7. Redémarrer les services
echo "🔄 Redémarrage des services..."

# Redémarrer Gunicorn
systemctl restart $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Redémarrer Nginx
systemctl restart nginx
systemctl enable nginx

echo "✅ Services redémarrés"

# 8. Vérifier le déploiement
echo "🔍 Vérification du déploiement..."
cd "$PROJECT_DIR"

# Script de vérification
cat > /tmp/verify_deployment.py << 'PYTHON_EOF'
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append('/var/www/kbis_immobilier')
django.setup()

from paiements.models_avance import AvanceLoyer

print("Vérification du déploiement...")

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

print("Vérification du déploiement terminée")
PYTHON_EOF

# Exécuter le script de vérification
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python /tmp/verify_deployment.py
else
    python3 /tmp/verify_deployment.py
fi

# Nettoyer le script temporaire
rm -f /tmp/verify_deployment.py

echo "✅ Vérification terminée"

# 9. Vérifier les services
echo "🔍 Vérification des services..."
systemctl is-active --quiet $SERVICE_NAME && echo "✅ Service $SERVICE_NAME actif" || echo "❌ Service $SERVICE_NAME inactif"
systemctl is-active --quiet nginx && echo "✅ Service nginx actif" || echo "❌ Service nginx inactif"

echo ""
echo "🎉 Correction des problèmes terminée !"
echo ""
echo "📋 Résumé des corrections :"
echo "   - Fichiers en conflit supprimés"
echo "   - Code mis à jour vers $AVANCES_BRANCH"
echo "   - Dépendances installées"
echo "   - Migrations appliquées"
echo "   - Données d'avances corrigées"
echo "   - Fichiers statiques collectés"
echo "   - Services redémarrés"
echo ""
echo "🚀 Votre application kbis_immobilier est maintenant opérationnelle !"
echo ""
echo "🌐 URLs importantes :"
echo "   - Application: http://votre-ip/"
echo "   - Création avance: http://votre-ip/paiements/avances/ajouter/"
echo "   - Admin: http://votre-ip/admin/"
echo ""
echo "✅ Déploiement des avances intelligentes réussi !"
