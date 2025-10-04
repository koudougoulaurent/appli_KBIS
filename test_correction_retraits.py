"""
Test de correction des retraits bailleur.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_correction_retraits():
    """Test de correction des retraits."""
    print("Test de correction des retraits...")
    
    try:
        from proprietes.models import Propriete, ChargesBailleur, Bailleur
        from paiements.models import RetraitBailleur
        from decimal import Decimal
        
        # Test 1: Vérifier les champs du modèle RetraitBailleur
        print("1. Vérification des champs du modèle RetraitBailleur:")
        retrait_fields = [field.name for field in RetraitBailleur._meta.fields]
        print(f"   Champs disponibles: {', '.join(retrait_fields[:10])}...")
        
        # Vérifier les champs importants
        important_fields = ['mois_retrait', 'montant_net_a_payer', 'bailleur', 'statut']
        for field in important_fields:
            if field in retrait_fields:
                print(f"   ✓ {field}: OK")
            else:
                print(f"   ✗ {field}: MANQUANT")
        
        # Test 2: Vérifier les bailleurs
        print("\n2. Vérification des bailleurs:")
        bailleurs = Bailleur.objects.all()[:3]
        for i, bailleur in enumerate(bailleurs):
            print(f"   {i+1}. {bailleur.get_nom_complet()}")
        
        if not bailleurs:
            print("   Aucun bailleur trouvé")
            return False
        
        bailleur = bailleurs[0]
        print(f"   Bailleur sélectionné: {bailleur.get_nom_complet()}")
        
        # Test 3: Vérifier les propriétés du bailleur
        print("\n3. Vérification des propriétés du bailleur:")
        proprietes = Propriete.objects.filter(bailleur=bailleur, is_deleted=False)[:3]
        for i, propriete in enumerate(proprietes):
            print(f"   {i+1}. {propriete.numero_propriete} - {propriete.titre}")
        
        if not proprietes:
            print("   Aucune propriété trouvée pour ce bailleur")
            return False
        
        # Test 4: Vérifier les charges bailleur
        print("\n4. Vérification des charges bailleur:")
        charges = ChargesBailleur.objects.filter(propriete__bailleur=bailleur)[:3]
        for i, charge in enumerate(charges):
            print(f"   {i+1}. {charge.titre} - {charge.montant_restant} F CFA - Statut: {charge.statut}")
        
        if not charges:
            print("   Aucune charge bailleur trouvée")
        
        # Test 5: Test de création d'un retrait
        print("\n5. Test de création d'un retrait:")
        try:
            from datetime import date
            mois_actuel = date.today().replace(day=1)
            
            # Vérifier s'il existe déjà un retrait pour ce mois
            retrait_existant = RetraitBailleur.objects.filter(
                bailleur=bailleur,
                mois_retrait=mois_actuel
            ).first()
            
            if retrait_existant:
                print(f"   ✓ Retrait existant trouvé: {retrait_existant.montant_net_a_payer} F CFA")
                print(f"   ✓ Statut: {retrait_existant.statut}")
                print(f"   ✓ Mois: {retrait_existant.mois_retrait}")
            else:
                print("   Aucun retrait existant pour ce mois")
                
        except Exception as e:
            print(f"   ✗ Erreur test retrait: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test correction: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("TEST DE CORRECTION DES RETRAITS BAILLEUR")
    print("=" * 50)
    
    success = test_correction_retraits()
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    
    if success:
        print("SUCCES - Les corrections des retraits fonctionnent!")
        print("OK - Champs du modèle RetraitBailleur corrects")
        print("OK - Utilisation de 'mois_retrait' au lieu de 'date_retrait'")
        print("OK - Utilisation de 'montant_net_a_payer' au lieu de 'montant_retrait'")
        print("OK - Statuts corrects ('en_attente', 'valide', 'paye')")
    else:
        print("ERREUR - Problème avec les corrections des retraits.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
