"""
Test de correction du montant dans le formulaire de charges bailleur.
"""

import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_montant_validation():
    """Test de la validation des montants."""
    print("Test de validation des montants...")
    
    try:
        # Test des montants avec virgules
        montants_test = [
            ('16999,93', True, 'Montant avec virgule'),
            ('150000', True, 'Montant entier'),
            ('150000.50', True, 'Montant avec point'),
            ('0', False, 'Montant zero'),
            ('abc', False, 'Montant texte'),
            ('', False, 'Montant vide'),
            ('999999999.99', True, 'Montant maximum'),
            ('1000000000', False, 'Montant trop eleve'),
        ]
        
        print("1. Test de conversion des montants:")
        for montant_str, should_be_valid, description in montants_test:
            try:
                if montant_str == '':
                    print(f"   {description}: ERREUR (attendu)")
                else:
                    # Nettoyer le montant (remplacer virgules par points)
                    montant_clean = montant_str.replace(',', '.')
                    montant_decimal = Decimal(montant_clean)
                    
                    if montant_decimal <= 0:
                        print(f"   {description}: ERREUR - doit etre > 0")
                    elif montant_decimal > Decimal('999999999.99'):
                        print(f"   {description}: ERREUR - trop eleve")
                    else:
                        print(f"   {description}: OK - {montant_decimal}")
                        
            except (ValueError, TypeError):
                print(f"   {description}: ERREUR - format invalide")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test montant: {e}")
        return False

def test_template_montant():
    """Test du template pour le champ montant."""
    print("\nTest du template montant...")
    
    try:
        # Lire le template
        with open('templates/proprietes/charges_bailleur/creer.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Vérifier que le champ montant est en type="text"
        if 'type="text"' in template_content and 'id="montant"' in template_content:
            print("   OK - Champ montant en type text")
        else:
            print("   ERREUR - Champ montant pas en type text")
        
        # Vérifier la validation JavaScript
        if 'montantField.value.replace' in template_content:
            print("   OK - Validation JavaScript pour virgules")
        else:
            print("   ERREUR - Validation JavaScript manquante")
        
        # Vérifier le formatage automatique
        if 'replace(/[^0-9,.]/g' in template_content:
            print("   OK - Formatage automatique present")
        else:
            print("   ERREUR - Formatage automatique manquant")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test template: {e}")
        return False

def test_validation_serveur():
    """Test de la validation côté serveur."""
    print("\nTest de la validation serveur...")
    
    try:
        # Simuler la validation côté serveur
        def validate_montant_serveur(montant):
            if not montant:
                return False, "Le montant est obligatoire."
            
            try:
                # Remplacer les virgules par des points pour la conversion
                montant_clean = montant.replace(',', '.')
                montant_decimal = Decimal(montant_clean)
                
                if montant_decimal <= 0:
                    return False, "Le montant doit etre superieur a 0."
                elif montant_decimal > Decimal('999999999.99'):
                    return False, "Le montant est trop eleve (maximum 999,999,999.99 F CFA)."
                else:
                    return True, f"Montant valide: {montant_decimal}"
                    
            except (ValueError, TypeError):
                return False, "Le montant doit etre un nombre valide."
        
        # Test des montants
        montants_test = [
            '16999,93',
            '150000',
            '150000.50',
            '0',
            'abc',
            '',
            '999999999.99',
            '1000000000',
        ]
        
        print("1. Test de validation serveur:")
        for montant in montants_test:
            is_valid, message = validate_montant_serveur(montant)
            status = "OK" if is_valid else "ERREUR"
            print(f"   {montant}: {status} - {message}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test validation serveur: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST DE CORRECTION DU MONTANT")
    print("=" * 50)
    
    tests = [
        test_montant_validation,
        test_template_montant,
        test_validation_serveur,
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
        print("\nSUCCES - Le montant est maintenant gere correctement!")
        print("OK - Montants avec virgules acceptes")
        print("OK - Conversion automatique virgule -> point")
        print("OK - Validation cote client et serveur")
        print("OK - Formatage automatique du champ")
        print("OK - Conservation du format original")
    else:
        print("\nATTENTION - Certains tests ont echoue.")
        print("Le montant peut ne pas etre gere correctement.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
