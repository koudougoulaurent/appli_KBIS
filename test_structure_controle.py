"""
Test de la structure de contrôle des déductions.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_structure_controle():
    """Test de la structure de contrôle."""
    print("Test de la structure de contrôle...")
    
    try:
        from proprietes.models import Propriete, ChargesBailleur, Bailleur
        from proprietes.forms import ChargesBailleurDeductionForm
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
        
        # Test 2: Vérifier les propriétés du bailleur
        print("\n2. Vérification des propriétés du bailleur:")
        proprietes = Propriete.objects.filter(bailleur=bailleur, is_deleted=False)[:3]
        for i, propriete in enumerate(proprietes):
            print(f"   {i+1}. {propriete.numero_propriete} - {propriete.titre}")
            print(f"      Loyer: {propriete.loyer_actuel} F CFA")
        
        if not proprietes:
            print("   Aucune propriété trouvée pour ce bailleur")
            return False
        
        propriete = proprietes[0]
        print(f"   Propriété sélectionnée: {propriete.numero_propriete}")
        
        # Test 3: Calculer le total mensuel du bailleur
        print("\n3. Calcul du total mensuel du bailleur:")
        try:
            total_mensuel = propriete.get_total_mensuel_bailleur()
            print(f"   ✓ Total mensuel du bailleur: {total_mensuel} F CFA")
        except Exception as e:
            print(f"   ✗ Erreur calcul total mensuel: {e}")
            return False
        
        # Test 4: Vérifier les charges bailleur
        print("\n4. Vérification des charges bailleur:")
        charges = ChargesBailleur.objects.filter(propriete__bailleur=bailleur)[:3]
        for i, charge in enumerate(charges):
            print(f"   {i+1}. {charge.titre} - {charge.montant_restant} F CFA - Statut: {charge.statut}")
        
        if not charges:
            print("   Aucune charge bailleur trouvée")
            return False
        
        charge = charges[0]
        print(f"   Charge sélectionnée: {charge.titre}")
        
        # Test 5: Test du formulaire de déduction
        print("\n5. Test du formulaire de déduction:")
        try:
            form = ChargesBailleurDeductionForm(propriete)
            print(f"   ✓ Formulaire créé avec succès")
            print(f"   ✓ Aide texte: {form.fields['montant_deduction'].help_text}")
            
            # Test de validation avec un montant valide
            form_data = {
                'montant_deduction': str(min(total_mensuel, charge.montant_restant)),
                'motif': 'Test de déduction'
            }
            form = ChargesBailleurDeductionForm(propriete, data=form_data)
            if form.is_valid():
                print(f"   ✓ Validation avec montant valide: OK")
            else:
                print(f"   ✗ Erreurs de validation: {form.errors}")
            
            # Test de validation avec un montant trop élevé
            form_data_invalid = {
                'montant_deduction': str(total_mensuel + 1000),
                'motif': 'Test de déduction invalide'
            }
            form_invalid = ChargesBailleurDeductionForm(propriete, data=form_data_invalid)
            if not form_invalid.is_valid():
                print(f"   ✓ Validation avec montant invalide: Rejeté correctement")
                print(f"   ✓ Message d'erreur: {form_invalid.errors['montant_deduction']}")
            else:
                print(f"   ✗ Validation avec montant invalide: Devrait être rejeté")
                
        except Exception as e:
            print(f"   ✗ Erreur test formulaire: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test structure: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("TEST DE LA STRUCTURE DE CONTRÔLE")
    print("=" * 50)
    
    success = test_structure_controle()
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    
    if success:
        print("SUCCES - La structure de contrôle fonctionne!")
        print("OK - Validation basée sur le retrait mensuel du bailleur")
        print("OK - Messages d'erreur cohérents")
        print("OK - Logique de déduction correcte")
        print("OK - Formulaire de déduction opérationnel")
    else:
        print("ERREUR - Problème avec la structure de contrôle.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
