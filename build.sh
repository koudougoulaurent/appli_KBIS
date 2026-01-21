#!/usr/bin/env bash
# Script de déploiement automatique pour Render
# Ce script s'exécute automatiquement à chaque déploiement

set -o errexit  # Arrête le script si une commande échoue

echo "====================================="
echo "🚀 DÉBUT DU DÉPLOIEMENT RENDER"
echo "====================================="

# 1. Installation des dépendances Python
echo "📦 Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Collecte des fichiers statiques
echo "📂 Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

# 3. Exécution des migrations de base de données
echo "🗄️  Exécution des migrations..."
python manage.py migrate --no-input

# 4. Synchronisation des consommations d'avances
echo "🔄 Synchronisation des consommations d'avances..."
python manage.py synchroniser_consommations_avances || echo "⚠️  Erreur non bloquante lors de la synchronisation des avances"

# 5. Correction des mois_paye manquants
echo "🔧 Correction des mois_paye manquants..."
python manage.py corriger_mois_paye_manquants || echo "⚠️  Erreur non bloquante lors de la correction des mois_paye manquants"

# 6. Correction des mois_paye incohérents
echo "🔧 Correction des mois_paye incohérents..."
python manage.py corriger_mois_paye_incoherents || echo "⚠️  Erreur non bloquante lors de la correction des mois_paye"

# 7. Recalcul des récapitulatifs avec charges bailleur
echo "🔢 Recalcul des récapitulatifs mensuels avec charges bailleur..."
python manage.py recalculer_recaps_avec_charges || echo "⚠️  Erreur non bloquante lors du recalcul des récapitulatifs"

# 8. Complétion automatique des reliquats de paiements partiels
echo "💰 Complétion des reliquats de paiements partiels..."
python manage.py completer_reliquats || echo "⚠️  Erreur non bloquante lors de la complétion des reliquats"

# 9. Régénération des récapitulatifs mensuels existants avec nouveau format groupé
echo "📊 Régénération des récapitulatifs mensuels..."
python manage.py regenerer_recapitulatifs_pdf --batch-size 5 || echo "⚠️  Aucun récapitulatif à régénérer ou erreur non bloquante"

# 10. Création du superuser si nécessaire (optionnel)
# Décommentez si vous voulez créer automatiquement un superuser
# echo "👤 Création du superuser..."
# python manage.py createsuperuser --no-input || echo "⚠️  Superuser existe déjà"

echo "====================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
echo "====================================="

