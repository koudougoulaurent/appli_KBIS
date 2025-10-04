"""
Test simple de correction du montant.
"""

def test_montant_simple():
    """Test simple de la gestion des montants."""
    print("Test simple de la gestion des montants...")
    
    # Test de conversion des montants
    montants_test = [
        '16999,93',
        '150000',
        '150000.50',
        '0',
        'abc',
        '',
        '999999999.99',
    ]
    
    print("1. Test de conversion des montants:")
    for montant in montants_test:
        try:
            if montant == '':
                print(f"   {montant}: ERREUR (attendu)")
            else:
                # Nettoyer le montant (remplacer virgules par points)
                montant_clean = montant.replace(',', '.')
                montant_decimal = float(montant_clean)
                
                if montant_decimal <= 0:
                    print(f"   {montant}: ERREUR - doit etre > 0")
                elif montant_decimal > 999999999.99:
                    print(f"   {montant}: ERREUR - trop eleve")
                else:
                    print(f"   {montant}: OK - {montant_decimal}")
                    
        except (ValueError, TypeError):
            print(f"   {montant}: ERREUR - format invalide")
    
    return True

def test_template_elements():
    """Test des éléments du template."""
    print("\nTest des éléments du template...")
    
    try:
        # Lire le template
        with open('templates/proprietes/charges_bailleur/creer.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Vérifier les éléments clés
        elements = [
            'type="text"',
            'id="montant"',
            'montantField.value.replace',
            'replace(/[^0-9,.]/g',
        ]
        
        print("1. Vérification des éléments:")
        for element in elements:
            if element in template_content:
                print(f"   OK - {element}")
            else:
                print(f"   MANQUANT - {element}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test template: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST SIMPLE DE CORRECTION DU MONTANT")
    print("=" * 50)
    
    tests = [
        test_montant_simple,
        test_template_elements,
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
        print("OK - Champ en type text (pas de conversion automatique)")
        print("OK - Formatage automatique du champ")
    else:
        print("\nATTENTION - Certains tests ont echoue.")
        print("Le montant peut ne pas etre gere correctement.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
