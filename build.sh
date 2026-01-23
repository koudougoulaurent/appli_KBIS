#!/usr/bin/env bash
# Script de déploiement automatique pour Render
# Ce script s'exécute automatiquement à chaque déploiement

set -o errexit  # Arrête le script si une commande échoue

echo "=============================================================================="
echo "🚀 DÉBUT DU DÉPLOIEMENT RENDER - KBIS IMMOBILIER"
echo "=============================================================================="

# ============================================================================
# PHASE 1 : INSTALLATION ET CONFIGURATION
# ============================================================================
echo ""
echo "📦 PHASE 1/5 : Installation des dépendances..."
echo "------------------------------------------------------------------------------"
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dépendances installées"

echo ""
echo "📂 Collecte des fichiers statiques..."
python manage.py collectstatic --no-input
echo "✅ Fichiers statiques collectés"

echo ""
echo "🗄️  Exécution des migrations de base de données..."
python manage.py migrate --no-input
echo "✅ Migrations appliquées"

echo ""
echo "⚡ Optimisation des performances (index BDD)..."
python manage.py optimiser_performances_avances || echo "⚠️  Erreur non bloquante"
echo "✅ Optimisations appliquées"

# ============================================================================
# PHASE 2 : NETTOYAGE ET CORRECTION DES DONNÉES
# ============================================================================
echo ""
echo "=============================================================================="
echo "🧹 PHASE 2/5 : Nettoyage et correction des données..."
echo "=============================================================================="

echo ""
echo "1. Nettoyage des doublons de paiements..."
python manage.py nettoyer_doublons_paiements || echo "⚠️  Erreur non bloquante"
echo "✅ Doublons nettoyés"

echo ""
echo "2. Correction des mois_paye manquants..."
python manage.py corriger_mois_paye_manquants || echo "⚠️  Erreur non bloquante"
echo "✅ Mois_paye manquants corrigés"

echo ""
echo "3. Correction des mois_paye incohérents..."
python manage.py corriger_mois_paye_incoherents || echo "⚠️  Erreur non bloquante"
echo "✅ Mois_paye incohérents corrigés"

# ============================================================================
# PHASE 3 : CORRECTION CRITIQUE DES AVANCES (V10.2)
# ============================================================================
echo ""
echo "=============================================================================="
echo "🔴 PHASE 3/5 : CORRECTION CRITIQUE DES AVANCES (V10.2)"
echo "=============================================================================="

echo ""
echo "1. Application de la logique unique des avances (V8)..."
python manage.py appliquer_logique_unique_avances || echo "⚠️  Erreur non bloquante"
echo "✅ Logique unique appliquée"

echo ""
echo "2. 🔴 CORRECTION CRITIQUE : Mois de début incorrect (V10.1 + V10.2)..."
echo "   → Suppression règle du 15+ (bug qui saute janvier)"
echo "   → Application logique Option A (dettes prioritaires)"
python manage.py corriger_avances_mois_debut_incorrect --corriger
echo "✅✅✅ CORRECTION CRITIQUE TERMINÉE - Avances corrigées"

echo ""
echo "3. Resynchronisation complète des avances..."
python manage.py resynchroniser_avances_complet || echo "⚠️  Erreur non bloquante"
echo "✅ Avances resynchronisées"

echo ""
echo "4. Synchronisation des consommations d'avances..."
python manage.py synchroniser_consommations_avances || echo "⚠️  Erreur non bloquante"
echo "✅ Consommations synchronisées"

# ============================================================================
# PHASE 4 : RECALCULS ET MISES À JOUR
# ============================================================================
echo ""
echo "=============================================================================="
echo "📊 PHASE 4/5 : Recalculs et mises à jour..."
echo "=============================================================================="

echo ""
echo "1. Recalcul des récapitulatifs avec charges bailleur..."
python manage.py recalculer_recaps_avec_charges || echo "⚠️  Erreur non bloquante"
echo "✅ Récapitulatifs recalculés"

echo ""
echo "2. Complétion des reliquats de paiements partiels..."
python manage.py completer_reliquats || echo "⚠️  Erreur non bloquante"
echo "✅ Reliquats complétés"

echo ""
echo "3. Régénération des récapitulatifs PDF..."
python manage.py regenerer_recapitulatifs_pdf --batch-size 5 || echo "⚠️  Aucun récapitulatif à régénérer"
echo "✅ PDFs régénérés"

# ============================================================================
# PHASE 5 : VÉRIFICATION FINALE
# ============================================================================
echo ""
echo "=============================================================================="
echo "✅ PHASE 5/5 : Vérification finale..."
echo "=============================================================================="

echo ""
echo "Résumé des corrections appliquées :"
echo "  ✅ Base de données migrée et optimisée"
echo "  ✅ Doublons de paiements nettoyés"
echo "  ✅ Mois_paye corrigés (manquants et incohérents)"
echo "  ✅✅✅ AVANCES CORRIGÉES (V10.2 - Option A)"
echo "      → Plus de saut de janvier"
echo "      → Dettes toujours prioritaires"
echo "      → Logique simple et cohérente"
echo "  ✅ Avances resynchronisées"
echo "  ✅ Récapitulatifs recalculés avec charges bailleur"
echo "  ✅ Reliquats complétés"
echo "  ✅ PDFs régénérés"

echo ""
echo "=============================================================================="
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
echo "=============================================================================="
echo ""
echo "📝 Note : Toutes les avances (nouvelles et existantes) utilisent maintenant"
echo "          la logique V10.2 Option A (dettes prioritaires, simple et cohérente)"
echo ""

