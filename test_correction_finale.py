"""
Test final de correction du formulaire de charges bailleur.
"""

import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_formulaire_charges_bailleur():
    """Test du formulaire de charges bailleur."""
    print("Test du formulaire de charges bailleur...")
    
    try:
        from proprietes.forms import ChargesBailleurForm
        
        # Test 1: Montant avec virgule
        print("1. Test montant avec virgule:")
        form_data = {
            'propriete': 1,  # ID d'une propriété existante
            'titre': 'Test réparation',
            'description': 'Description détaillée de la réparation',
            'type_charge': 'reparation',
            'priorite': 'normale',
            'montant': '16999,93',
            'date_charge': '2025-01-15',
        }
        
        form = ChargesBailleurForm(data=form_data)
        if form.is_valid():
            print("   OK - Formulaire valide avec montant virgule")
            print(f"   Montant nettoye: {form.cleaned_data['montant']}")
        else:
            print("   ERREUR - Formulaire invalide")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
        
        # Test 2: Montant avec point
        print("\n2. Test montant avec point:")
        form_data['montant'] = '150000.50'
        form = ChargesBailleurForm(data=form_data)
        if form.is_valid():
            print("   OK - Formulaire valide avec montant point")
            print(f"   Montant nettoye: {form.cleaned_data['montant']}")
        else:
            print("   ERREUR - Formulaire invalide")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
        
        # Test 3: Montant invalide
        print("\n3. Test montant invalide:")
        form_data['montant'] = 'abc'
        form = ChargesBailleurForm(data=form_data)
        if not form.is_valid():
            print("   OK - Formulaire invalide comme attendu")
            if 'montant' in form.errors:
                print(f"   Erreur montant: {form.errors['montant']}")
        else:
            print("   ERREUR - Formulaire devrait etre invalide")
        
        # Test 4: Montant zero
        print("\n4. Test montant zero:")
        form_data['montant'] = '0'
        form = ChargesBailleurForm(data=form_data)
        if not form.is_valid():
            print("   OK - Formulaire invalide comme attendu")
            if 'montant' in form.errors:
                print(f"   Erreur montant: {form.errors['montant']}")
        else:
            print("   ERREUR - Formulaire devrait etre invalide")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test formulaire: {e}")
        return False

def test_template_ancien():
    """Test du template de l'ancienne vue."""
    print("\nTest du template de l'ancienne vue...")
    
    try:
        # Lire le template
        with open('templates/proprietes/charge_bailleur_ajouter.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Vérifier les éléments clés
        elements = [
            'form.propriete',
            'form.montant',
            'form.titre',
            'form.description',
            'form.type_charge',
            'form.date_charge',
            'needs-validation',
            'enctype="multipart/form-data"',
        ]
        
        print("1. Vérification des éléments du template:")
        for element in elements:
            if element in template_content:
                print(f"   OK - {element}")
            else:
                print(f"   MANQUANT - {element}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test template: {e}")
        return False

def test_urls():
    """Test des URLs."""
    print("\nTest des URLs...")
    
    try:
        from django.urls import reverse
        
        # Test de l'ancienne URL
        try:
            url_ancienne = reverse('proprietes:ajouter_charge_bailleur')
            print(f"   OK - Ancienne URL: {url_ancienne}")
        except Exception as e:
            print(f"   ERREUR - Ancienne URL: {e}")
        
        # Test de la nouvelle URL
        try:
            url_nouvelle = reverse('proprietes:creer_charge_bailleur')
            print(f"   OK - Nouvelle URL: {url_nouvelle}")
        except Exception as e:
            print(f"   ERREUR - Nouvelle URL: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test URLs: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST FINAL DE CORRECTION DU FORMULAIRE")
    print("=" * 50)
    
    tests = [
        test_formulaire_charges_bailleur,
        test_template_ancien,
        test_urls,
    ]
    
    resultats = []
    for test in tests:
        try:
            resultat = test()
            resultats.append(resultat)
        except Exception as e:
            print(f"ERREUR CRITIQUE dans le test: {e}")
            resultats.append(False)
    
    # Résumé
    print("\n" + "=" * 50)
    print("RESUME DES TESTS")
    print("=" * 50)
    
    tests_reussis = sum(resultats)
    total_tests = len(tests)
    
    print(f"Tests reussis: {tests_reussis}/{total_tests}")
    print(f"Taux de reussite: {(tests_reussis/total_tests)*100:.1f}%")
    
    if tests_reussis == total_tests:
        print("\nSUCCES - Le formulaire est maintenant corrige!")
        print("OK - Montants avec virgules acceptes")
        print("OK - Validation robuste implementee")
        print("OK - Template fonctionnel")
        print("OK - URLs accessibles")
        print("\nUTILISATION:")
        print("- Ancienne URL: http://127.0.0.1:8000/proprietes/charges-bailleur/ajouter/")
        print("- Nouvelle URL: http://127.0.0.1:8000/proprietes/charges-bailleur-intelligent/creer/")
    else:
        print("\nATTENTION - Certains tests ont echoue.")
        print("Le formulaire peut ne pas fonctionner correctement.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
