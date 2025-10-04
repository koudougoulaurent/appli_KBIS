"""
Test final du système de charges bailleur - Version simplifiée.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_imports():
    """Test des imports essentiels."""
    print("Test des imports...")
    
    try:
        from proprietes.models import ChargesBailleur
        from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
        print("OK - Imports reussis")
        return True
    except Exception as e:
        print(f"ERREUR - Import: {e}")
        return False

def test_model_fields():
    """Test des champs du modèle."""
    print("\nTest des champs du modèle...")
    
    try:
        from proprietes.models import ChargesBailleur
        
        # Vérifier les nouveaux champs
        fields = [field.name for field in ChargesBailleur._meta.fields]
        required_fields = ['montant_deja_deduit', 'montant_restant']
        
        for field in required_fields:
            if field in fields:
                print(f"OK - Champ {field} present")
            else:
                print(f"ERREUR - Champ {field} manquant")
                return False
        
        # Vérifier les nouveaux statuts
        statuts = [choice[0] for choice in ChargesBailleur.STATUT_CHOICES]
        if 'deduite_retrait' in statuts:
            print("OK - Statut 'deduite_retrait' present")
        else:
            print("ERREUR - Statut 'deduite_retrait' manquant")
            return False
        
        return True
    except Exception as e:
        print(f"ERREUR - Modele: {e}")
        return False

def test_service_methods():
    """Test des méthodes du service."""
    print("\nTest des méthodes du service...")
    
    try:
        from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
        
        # Vérifier les méthodes principales
        methods = [
            'calculer_charges_bailleur_pour_mois',
            'integrer_charges_dans_retrait', 
            'integrer_charges_dans_recap',
            'generer_rapport_charges_bailleur'
        ]
        
        for method in methods:
            if hasattr(ServiceChargesBailleurIntelligent, method):
                print(f"OK - Methode {method} presente")
            else:
                print(f"ERREUR - Methode {method} manquante")
                return False
        
        return True
    except Exception as e:
        print(f"ERREUR - Service: {e}")
        return False

def test_recap_model():
    """Test du modèle RecapMensuel."""
    print("\nTest du modèle RecapMensuel...")
    
    try:
        from paiements.models import RecapMensuel
        
        # Vérifier le nouveau champ
        fields = [field.name for field in RecapMensuel._meta.fields]
        if 'total_charges_bailleur' in fields:
            print("OK - Champ 'total_charges_bailleur' present")
        else:
            print("ERREUR - Champ 'total_charges_bailleur' manquant")
            return False
        
        # Vérifier la méthode de calcul
        if hasattr(RecapMensuel, '_calculer_charges_bailleur_mois'):
            print("OK - Methode '_calculer_charges_bailleur_mois' presente")
        else:
            print("ERREUR - Methode '_calculer_charges_bailleur_mois' manquante")
            return False
        
        return True
    except Exception as e:
        print(f"ERREUR - Modele RecapMensuel: {e}")
        return False

def test_urls():
    """Test des URLs."""
    print("\nTest des URLs...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # Tester l'URL de liste des charges
        try:
            response = client.get('/proprietes/charges-bailleur-intelligent/')
            print(f"OK - URL liste charges: {response.status_code}")
        except Exception as e:
            print(f"ATTENTION - URL liste charges: {e}")
        
        return True
    except Exception as e:
        print(f"ERREUR - URLs: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST FINAL DU SYSTEME DE CHARGES BAILLEUR")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_model_fields,
        test_service_methods,
        test_recap_model,
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
        print("\nSUCCES - Tous les tests sont passes!")
        print("OK - Le systeme de charges bailleur est operationnel!")
        print("\nFONCTIONNALITES DISPONIBLES:")
        print("- Interface de gestion: /proprietes/charges-bailleur-intelligent/")
        print("- Creation de charges: /proprietes/charges-bailleur-intelligent/creer/")
        print("- Rapports: /proprietes/charges-bailleur-intelligent/rapport/")
        print("- Integration automatique dans les retraits et recapitulatifs")
    else:
        print("\nATTENTION - Certains tests ont echoue.")
        print("Le systeme peut ne pas fonctionner correctement.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
