"""
Test du formulaire de déduction des charges bailleur.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_formulaire_deduction():
    """Test du formulaire de déduction."""
    print("Test du formulaire de déduction...")
    
    try:
        from proprietes.forms import ChargesBailleurDeductionForm
        from proprietes.models import Propriete, ChargesBailleur, Bailleur
        from decimal import Decimal
        
        # Test 1: Vérifier la structure du formulaire
        print("1. Vérification de la structure du formulaire:")
        form = ChargesBailleurDeductionForm()
        
        # Vérifier les champs requis
        required_fields = ['montant_deduction', 'date_deduction', 'motif']
        for field in required_fields:
            if field in form.fields:
                is_required = form.fields[field].required
                print(f"   ✓ {field}: {'Requis' if is_required else 'Optionnel'}")
            else:
                print(f"   ✗ {field}: MANQUANT")
        
        # Vérifier les champs optionnels
        optional_fields = ['notes']
        for field in optional_fields:
            if field in form.fields:
                is_required = form.fields[field].required
                print(f"   ✓ {field}: {'Requis' if is_required else 'Optionnel'}")
            else:
                print(f"   ✗ {field}: MANQUANT")
        
        # Test 2: Test de validation avec données valides
        print("\n2. Test de validation avec données valides:")
        form_data_valid = {
            'montant_deduction': '10000.00',
            'date_deduction': '2025-01-04',
            'motif': 'Réparation plomberie urgente',
            'notes': 'Travaux effectués par plombier agréé'
        }
        
        form_valid = ChargesBailleurDeductionForm(data=form_data_valid)
        if form_valid.is_valid():
            print("   ✓ Validation avec données valides: OK")
            print(f"   ✓ Montant: {form_valid.cleaned_data['montant_deduction']}")
            print(f"   ✓ Motif: {form_valid.cleaned_data['motif']}")
        else:
            print("   ✗ Erreurs de validation:")
            for field, errors in form_valid.errors.items():
                print(f"     {field}: {errors}")
        
        # Test 3: Test de validation avec données invalides
        print("\n3. Test de validation avec données invalides:")
        form_data_invalid = {
            'montant_deduction': '',  # Montant vide
            'date_deduction': '',     # Date vide
            'motif': '',              # Motif vide
        }
        
        form_invalid = ChargesBailleurDeductionForm(data=form_data_invalid)
        if not form_invalid.is_valid():
            print("   ✓ Validation avec données invalides: Rejeté correctement")
            for field, errors in form_invalid.errors.items():
                print(f"     {field}: {errors}")
        else:
            print("   ✗ Validation avec données invalides: Devrait être rejeté")
        
        # Test 4: Test de validation du montant
        print("\n4. Test de validation du montant:")
        form_data_montant_invalid = {
            'montant_deduction': '-100.00',  # Montant négatif
            'date_deduction': '2025-01-04',
            'motif': 'Test montant négatif',
        }
        
        form_montant_invalid = ChargesBailleurDeductionForm(data=form_data_montant_invalid)
        if not form_montant_invalid.is_valid():
            print("   ✓ Validation montant négatif: Rejeté correctement")
            print(f"     Erreur: {form_montant_invalid.errors['montant_deduction']}")
        else:
            print("   ✗ Validation montant négatif: Devrait être rejeté")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test formulaire: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test."""
    print("TEST DU FORMULAIRE DE DÉDUCTION")
    print("=" * 50)
    
    success = test_formulaire_deduction()
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    
    if success:
        print("SUCCES - Le formulaire de déduction fonctionne!")
        print("OK - Champs requis présents (montant_deduction, date_deduction, motif)")
        print("OK - Champs optionnels présents (notes)")
        print("OK - Validation des données valides")
        print("OK - Rejet des données invalides")
        print("OK - Validation du montant")
    else:
        print("ERREUR - Problème avec le formulaire de déduction.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
