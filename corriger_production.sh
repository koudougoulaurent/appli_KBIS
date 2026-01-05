#!/bin/bash
# Script de correction rapide pour Render
# À exécuter dans le shell Render

echo "🔧 CORRECTION RAPIDE DES AVANCES DE LOYER"
echo "=========================================="
echo ""

# 1. Diagnostic
echo "📊 Étape 1/2 : Diagnostic..."
python manage.py corriger_avances

echo ""
echo "⏸️  Appuyez sur Entrée pour continuer avec la correction automatique..."
read

# 2. Correction
echo ""
echo "✅ Étape 2/2 : Correction automatique..."
python manage.py corriger_avances --auto-fix

echo ""
echo "=========================================="
echo "✅ TERMINÉ !"
echo ""
echo "🔍 Vérifiez maintenant :"
echo "   1. Allez sur la page du contrat concerné"
echo "   2. Cliquez sur 'Ajouter un paiement'"
echo "   3. Le prochain paiement devrait être 'Décembre 2025'"
echo ""
