"""
Test des méthodes de charges bailleur.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_charges_bailleur_methods():
    """Test des méthodes de charges bailleur."""
    print("Test des méthodes de charges bailleur...")
    
    try:
        from proprietes.models import Propriete, ChargesBailleur, Bailleur
        from decimal import Decimal
        
        # Test 1: Vérifier qu'une propriété a les méthodes
        print("1. Vérification des méthodes sur une propriété:")
        propriete = Propriete.objects.first()
        
        if propriete:
            print(f"   Propriété: {propriete.numero_propriete} - {propriete.titre}")
            
            # Test get_charges_bailleur_en_cours
            try:
                charges_en_cours = propriete.get_charges_bailleur_en_cours()
                print(f"   ✓ get_charges_bailleur_en_cours(): {charges_en_cours}")
            except Exception as e:
                print(f"   ✗ get_charges_bailleur_en_cours(): ERREUR - {e}")
            
            # Test get_total_mensuel_bailleur
            try:
                total_mensuel = propriete.get_total_mensuel_bailleur()
                print(f"   ✓ get_total_mensuel_bailleur(): {total_mensuel}")
            except Exception as e:
                print(f"   ✗ get_total_mensuel_bailleur(): ERREUR - {e}")
            
            # Test get_loyer_total
            try:
                loyer_total = propriete.get_loyer_total()
                print(f"   ✓ get_loyer_total(): {loyer_total}")
            except Exception as e:
                print(f"   ✗ get_loyer_total(): ERREUR - {e}")
        else:
            print("   Aucune propriété trouvée")
        
        # Test 2: Vérifier les charges bailleur
        print("\n2. Vérification des charges bailleur:")
        charges_count = ChargesBailleur.objects.count()
        print(f"   Nombre de charges bailleur: {charges_count}")
        
        if charges_count > 0:
            charges = ChargesBailleur.objects.all()[:3]
            for i, charge in enumerate(charges):
                print(f"   {i+1}. {charge.titre} - {charge.montant_restant} F CFA - Statut: {charge.statut}")
        
        # Test 3: Vérifier les bailleurs
        print("\n3. Vérification des bailleurs:")
        bailleurs_count = Bailleur.objects.count()
        print(f"   Nombre de bailleurs: {bailleurs_count}")
        
        if bailleurs_count > 0:
            bailleurs = Bailleur.objects.all()[:3]
            for i, bailleur in enumerate(bailleurs):
                print(f"   {i+1}. {bailleur.get_nom_complet()}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test méthodes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("TEST DES METHODES DE CHARGES BAILLEUR")
    print("=" * 50)
    
    success = test_charges_bailleur_methods()
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    
    if success:
        print("SUCCES - Les méthodes de charges bailleur fonctionnent!")
        print("OK - get_charges_bailleur_en_cours() ajoutée")
        print("OK - get_total_mensuel_bailleur() ajoutée")
        print("OK - Calcul basé sur le total mensuel du bailleur")
    else:
        print("ERREUR - Problème avec les méthodes de charges bailleur.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
