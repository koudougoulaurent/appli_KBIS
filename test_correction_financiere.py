#!/usr/bin/env python
"""
Script de test pour vérifier la correction des montants financiers
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Bailleur, Propriete
from contrats.models import Contrat
from paiements.models import RecapitulatifMensuelBailleur
from decimal import Decimal
from datetime import date

def test_correction_financiere():
    """Test de la correction des montants financiers."""
    
    print("🔍 Test de la correction des montants financiers")
    print("=" * 60)
    
    # Récupérer un bailleur avec des propriétés
    bailleur = Bailleur.objects.filter(
        proprietes__contrats__est_actif=True
    ).first()
    
    if not bailleur:
        print("❌ Aucun bailleur avec des propriétés actives trouvé")
        return False
    
    print(f"✅ Bailleur testé: {bailleur.get_nom_complet()}")
    
    # Récupérer les propriétés avec contrats actifs
    proprietes_actives = Propriete.objects.filter(
        bailleur=bailleur,
        contrats__est_actif=True
    ).distinct()
    
    print(f"✅ Propriétés actives: {proprietes_actives.count()}")
    
    # Vérifier les montants des contrats
    total_loyers_contrats = Decimal('0')
    total_charges_contrats = Decimal('0')
    
    for propriete in proprietes_actives:
        contrat = propriete.contrats.filter(est_actif=True).first()
        if contrat:
            loyer = contrat.loyer_mensuel or Decimal('0')
            charges = contrat.charges_mensuelles or Decimal('0')
            total_loyers_contrats += loyer
            total_charges_contrats += charges
            
            print(f"  📍 {propriete.adresse}")
            print(f"     Loyer: {loyer} F CFA")
            print(f"     Charges: {charges} F CFA")
            print(f"     Locataire: {contrat.locataire.get_nom_complet()}")
    
    print(f"\n💰 Totaux des contrats:")
    print(f"   Loyers: {total_loyers_contrats} F CFA")
    print(f"   Charges: {total_charges_contrats} F CFA")
    print(f"   Net: {total_loyers_contrats - total_charges_contrats} F CFA")
    
    # Créer un récapitulatif de test
    mois_test = date(2024, 1, 1)  # Janvier 2024
    
    # Vérifier si un récapitulatif existe déjà
    recap_existant = RecapitulatifMensuelBailleur.objects.filter(
        bailleur=bailleur,
        mois_recapitulatif=mois_test
    ).first()
    
    if recap_existant:
        print(f"\n📊 Récapitulatif existant trouvé pour {mois_test.strftime('%B %Y')}")
        recap = recap_existant
    else:
        print(f"\n📊 Création d'un récapitulatif de test pour {mois_test.strftime('%B %Y')}")
        recap = RecapitulatifMensuelBailleur.objects.create(
            bailleur=bailleur,
            mois_recapitulatif=mois_test,
            type_recapitulatif='mensuel',
            statut='en_preparation'
        )
    
    # Calculer les totaux avec la nouvelle logique
    totaux = recap.calculer_totaux_bailleur()
    
    print(f"\n📈 Résultats du calcul:")
    print(f"   Nombre de propriétés: {totaux['nombre_proprietes']}")
    print(f"   Loyers attendus: {totaux['total_loyers_bruts']} F CFA")
    print(f"   Charges déductibles: {totaux['total_charges_deductibles']} F CFA")
    print(f"   Charges bailleur: {totaux['total_charges_bailleur']} F CFA")
    print(f"   Montant net: {totaux['total_net_a_payer']} F CFA")
    
    # Vérifier que les montants ne sont plus à 0
    if totaux['total_loyers_bruts'] > 0:
        print("\n✅ SUCCÈS: Les montants ne sont plus à 0!")
        print("✅ La correction fonctionne correctement")
        return True
    else:
        print("\n❌ ÉCHEC: Les montants sont toujours à 0")
        print("❌ La correction n'a pas fonctionné")
        return False

def test_affichage_template():
    """Test de l'affichage dans le template."""
    
    print("\n🎨 Test de l'affichage template")
    print("=" * 40)
    
    # Récupérer un récapitulatif existant
    recap = RecapitulatifMensuelBailleur.objects.filter(
        bailleur__proprietes__contrats__est_actif=True
    ).first()
    
    if not recap:
        print("❌ Aucun récapitulatif trouvé pour le test")
        return False
    
    # Calculer les totaux
    totaux = recap.calculer_totaux_bailleur()
    
    print(f"✅ Récapitulatif testé: {recap}")
    print(f"✅ Bailleur: {totaux['bailleur'].get_nom_complet()}")
    print(f"✅ Propriétés: {totaux['nombre_proprietes']}")
    
    # Vérifier les détails des propriétés
    for i, detail in enumerate(totaux['details_proprietes'], 1):
        print(f"\n  📍 Propriété {i}:")
        print(f"     Adresse: {detail['propriete'].adresse}")
        print(f"     Locataire: {detail['locataire'].get_nom_complet()}")
        print(f"     Loyer attendu: {detail['loyers_bruts']} F CFA")
        print(f"     Charges déductibles: {detail['charges_deductibles']} F CFA")
        print(f"     Montant net: {detail['montant_net']} F CFA")
    
    return True

if __name__ == "__main__":
    print("🚀 Démarrage des tests de correction financière")
    print("=" * 60)
    
    try:
        # Test 1: Correction des calculs
        test1_success = test_correction_financiere()
        
        # Test 2: Affichage template
        test2_success = test_affichage_template()
        
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS")
        print("=" * 60)
        print(f"Test calculs financiers: {'✅ RÉUSSI' if test1_success else '❌ ÉCHOUÉ'}")
        print(f"Test affichage template: {'✅ RÉUSSI' if test2_success else '❌ ÉCHOUÉ'}")
        
        if test1_success and test2_success:
            print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
            print("✅ La correction des montants financiers fonctionne correctement")
        else:
            print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
            print("❌ Vérifiez les corrections apportées")
            
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
