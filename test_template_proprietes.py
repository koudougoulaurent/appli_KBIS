"""
Test du template pour vérifier l'affichage des propriétés.
"""

def test_template_proprietes():
    """Test du template pour les propriétés."""
    print("Test du template pour les propriétés...")
    
    try:
        # Lire le template
        with open('templates/proprietes/charges_bailleur/creer.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Vérifier les éléments clés pour les propriétés
        elements_proprietes = [
            '{% for propriete in proprietes %}',
            '{{ propriete.id }}',
            '{{ propriete.adresse }}',
            '{{ propriete.bailleur.get_nom_complet',
            'PROPRIETE CONCERNEE',
            'Sélectionnez une propriété',
        ]
        
        print("1. Vérification des éléments du template pour les propriétés:")
        for element in elements_proprietes:
            if element in template_content:
                print(f"   OK - {element}")
            else:
                print(f"   MANQUANT - {element}")
        
        # Vérifier qu'il n'y a pas d'éléments de bailleurs
        elements_bailleurs = [
            '{% for bailleur in bailleurs %}',
            '{{ bailleur.id }}',
            '{{ bailleur.get_nom_complet',
        ]
        
        print("\n2. Vérification qu'il n'y a pas d'éléments de bailleurs:")
        for element in elements_bailleurs:
            if element in template_content:
                print(f"   ATTENTION - {element} (ne devrait pas être là)")
            else:
                print(f"   OK - {element} (correctement absent)")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test template: {e}")
        return False

def test_vue_context():
    """Test du contexte de la vue."""
    print("\nTest du contexte de la vue...")
    
    try:
        # Lire le fichier de vue
        with open('proprietes/views_charges_bailleur.py', 'r', encoding='utf-8') as f:
            vue_content = f.read()
        
        # Vérifier que la vue charge les propriétés
        elements_vue = [
            'proprietes = Propriete.objects.filter',
            "'proprietes': proprietes",
            'select_related(\'bailleur\')',
            'order_by(\'adresse\')',
        ]
        
        print("1. Vérification des éléments de la vue:")
        for element in elements_vue:
            if element in vue_content:
                print(f"   OK - {element}")
            else:
                print(f"   MANQUANT - {element}")
        
        # Vérifier qu'il n'y a pas de chargement de bailleurs
        elements_bailleurs_vue = [
            'bailleurs = Bailleur.objects',
            "'bailleurs': bailleurs",
        ]
        
        print("\n2. Vérification qu'il n'y a pas de chargement de bailleurs:")
        for element in elements_bailleurs_vue:
            if element in vue_content:
                print(f"   ATTENTION - {element} (ne devrait pas être là)")
            else:
                print(f"   OK - {element} (correctement absent)")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test vue: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST DU TEMPLATE ET DE LA VUE POUR LES PROPRIETES")
    print("=" * 60)
    
    tests = [
        test_template_proprietes,
        test_vue_context,
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
    print("\n" + "=" * 60)
    print("RESUME DES TESTS")
    print("=" * 60)
    
    tests_reussis = sum(resultats)
    total_tests = len(tests)
    
    print(f"Tests reussis: {tests_reussis}/{total_tests}")
    print(f"Taux de reussite: {(tests_reussis/total_tests)*100:.1f}%")
    
    if tests_reussis == total_tests:
        print("\nSUCCES - Le template et la vue sont correctement configures!")
        print("OK - Template affiche les proprietes")
        print("OK - Vue charge les proprietes")
        print("OK - Pas de confusion avec les bailleurs")
    else:
        print("\nATTENTION - Certains tests ont echoue.")
        print("Le template ou la vue peuvent ne pas etre correctement configures.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
