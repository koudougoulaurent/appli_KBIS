#!/usr/bin/env python
"""
Script de test pour verifier le formulaire d'unite
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.forms_unites import UniteLocativeForm
from proprietes.models import Propriete

def test_form():
    """Teste la creation du formulaire"""
    print("Test du formulaire UniteLocativeForm...")
    
    try:
        # Test 1: Formulaire sans donnees
        form = UniteLocativeForm()
        print("✓ Formulaire cree sans erreur")
        
        # Test 2: Verifier que le helper existe
        if hasattr(form, 'helper'):
            print("✓ Helper crispy forms present")
        else:
            print("✗ Helper crispy forms manquant")
            
        # Test 3: Verifier les champs
        print(f"Champs du formulaire: {list(form.fields.keys())}")
        
        # Test 4: Test avec une propriete
        try:
            propriete = Propriete.objects.first()
            if propriete:
                initial = {'propriete': propriete}
                form_with_initial = UniteLocativeForm(initial=initial)
                print("✓ Formulaire avec initial cree sans erreur")
            else:
                print("⚠ Aucune propriete trouvee pour le test")
        except Exception as e:
            print(f"✗ Erreur avec initial: {e}")
            
        # Test 5: Test des champs individuels
        for field_name, field in form.fields.items():
            try:
                # Simuler l'utilisation de as_crispy_field
                if hasattr(field, 'form'):
                    print(f"✓ Champ {field_name}: OK")
                else:
                    print(f"✗ Champ {field_name}: Pas d'attribut form")
            except Exception as e:
                print(f"✗ Champ {field_name}: Erreur - {e}")
                
    except Exception as e:
        print(f"✗ Erreur generale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_form()
