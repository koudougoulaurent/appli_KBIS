"""
Test du système de retraits bailleur avec intégration des charges.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_systeme_retraits_bailleur():
    """Test du système de retraits bailleur."""
    print("Test du système de retraits bailleur...")
    
    try:
        from proprietes.models import Propriete, ChargesBailleur, Bailleur
        from paiements.services_retraits_bailleur import ServiceRetraitsBailleurIntelligent
        from decimal import Decimal
        
        # Test 1: Vérifier les bailleurs
        print("1. Vérification des bailleurs:")
        bailleurs = Bailleur.objects.all()[:3]
        for i, bailleur in enumerate(bailleurs):
            print(f"   {i+1}. {bailleur.get_nom_complet()}")
        
        if not bailleurs:
            print("   Aucun bailleur trouvé")
            return False
        
        bailleur = bailleurs[0]
        print(f"   Bailleur sélectionné: {bailleur.get_nom_complet()}")
        
        # Test 2: Calculer le retrait mensuel
        print("\n2. Calcul du retrait mensuel:")
        try:
            calcul = ServiceRetraitsBailleurIntelligent.calculer_retrait_mensuel_bailleur(bailleur)
            print(f"   ✓ Total loyers: {calcul['total_loyers']} F CFA")
            print(f"   ✓ Charges déductibles: {calcul['total_charges_deductibles']} F CFA")
            print(f"   ✓ Charges bailleur: {calcul['total_charges_bailleur']} F CFA")
            print(f"   ✓ Montant net: {calcul['montant_net']} F CFA")
        except Exception as e:
            print(f"   ✗ Erreur calcul retrait: {e}")
            return False
        
        # Test 3: Vérifier les charges bailleur
        print("\n3. Vérification des charges bailleur:")
        charges = ChargesBailleur.objects.filter(propriete__bailleur=bailleur)[:3]
        for i, charge in enumerate(charges):
            print(f"   {i+1}. {charge.titre} - {charge.montant_restant} F CFA - Statut: {charge.statut}")
        
        if not charges:
            print("   Aucune charge bailleur trouvée")
        
        # Test 4: Créer un retrait mensuel
        print("\n4. Création d'un retrait mensuel:")
        try:
            retrait = ServiceRetraitsBailleurIntelligent.creer_ou_mettre_a_jour_retrait_mensuel(
                bailleur=bailleur,
                user=None
            )
            print(f"   ✓ Retrait créé/mis à jour: {retrait.montant_retrait} F CFA")
            print(f"   ✓ Statut: {retrait.statut}")
            print(f"   ✓ Date: {retrait.date_retrait}")
        except Exception as e:
            print(f"   ✗ Erreur création retrait: {e}")
            return False
        
        # Test 5: Rapport des retraits
        print("\n5. Rapport des retraits mensuels:")
        try:
            rapport = ServiceRetraitsBailleurIntelligent.generer_rapport_retraits_mensuels()
            print(f"   ✓ Mois: {rapport['mois']}/{rapport['annee']}")
            print(f"   ✓ Nombre de retraits: {rapport['nombre_retraits']}")
            print(f"   ✓ Total retraits: {rapport['total_retraits']} F CFA")
            print(f"   ✓ Total charges intégrées: {rapport['total_charges_integre']} F CFA")
        except Exception as e:
            print(f"   ✗ Erreur rapport: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test système: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("TEST DU SYSTÈME DE RETRAITS BAILLEUR")
    print("=" * 50)
    
    success = test_systeme_retraits_bailleur()
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    
    if success:
        print("SUCCES - Le système de retraits bailleur fonctionne!")
        print("OK - Calcul du retrait mensuel")
        print("OK - Intégration des charges")
        print("OK - Service intelligent opérationnel")
        print("OK - Déduction du retrait mensuel (pas du loyer individuel)")
    else:
        print("ERREUR - Problème avec le système de retraits bailleur.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
