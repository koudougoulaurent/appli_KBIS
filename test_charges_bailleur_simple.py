"""
Test simple du système de charges bailleur.
"""

import os
import sys
import django
from datetime import date
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_imports():
    """Test des imports."""
    print("Test des imports...")
    
    try:
        from proprietes.models import ChargesBailleur, Bailleur, Propriete
        from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
        print("OK - Imports reussis")
        return True
    except Exception as e:
        print(f"ERREUR - Import: {e}")
        return False

def test_model_charges_bailleur():
    """Test du modèle ChargesBailleur."""
    print("\nTest du modèle ChargesBailleur...")
    
    try:
        from proprietes.models import ChargesBailleur
        
        # Vérifier que le modèle a les nouveaux champs
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

def test_service_charges_bailleur():
    """Test du service des charges bailleur."""
    print("\nTest du service des charges bailleur...")
    
    try:
        from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
        from proprietes.models import Bailleur
        
        # Vérifier que le service a les méthodes principales
        methods = ['calculer_charges_bailleur_pour_mois', 'integrer_charges_dans_retrait', 'integrer_charges_dans_recap']
        
        for method in methods:
            if hasattr(ServiceChargesBailleurIntelligent, method):
                print(f"OK - Methode {method} presente")
            else:
                print(f"ERREUR - Methode {method} manquante")
                return False
        
        # Test avec un bailleur existant
        bailleur = Bailleur.objects.first()
        if bailleur:
            mois_actuel = date.today().replace(day=1)
            resultat = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(bailleur, mois_actuel)
            print(f"OK - Calcul des charges reussi pour {bailleur.get_nom_complet()}")
            print(f"   Total charges: {resultat['total_charges']} F CFA")
            print(f"   Nombre de charges: {resultat['nombre_charges']}")
        else:
            print("ATTENTION - Aucun bailleur trouve pour le test")
        
        return True
    except Exception as e:
        print(f"ERREUR - Service: {e}")
        return False

def test_model_recap_mensuel():
    """Test du modèle RecapMensuel."""
    print("\nTest du modèle RecapMensuel...")
    
    try:
        from paiements.models import RecapMensuel
        
        # Vérifier que le modèle a le nouveau champ
        fields = [field.name for field in RecapMensuel._meta.fields]
        if 'total_charges_bailleur' in fields:
            print("OK - Champ 'total_charges_bailleur' present")
        else:
            print("ERREUR - Champ 'total_charges_bailleur' manquant")
            return False
        
        # Vérifier que la méthode de calcul existe
        if hasattr(RecapMensuel, '_calculer_charges_bailleur_mois'):
            print("OK - Methode '_calculer_charges_bailleur_mois' presente")
        else:
            print("ERREUR - Methode '_calculer_charges_bailleur_mois' manquante")
            return False
        
        return True
    except Exception as e:
        print(f"ERREUR - Modele RecapMensuel: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST SIMPLE DU SYSTEME DE CHARGES BAILLEUR")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_model_charges_bailleur,
        test_service_charges_bailleur,
        test_model_recap_mensuel,
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
        print("SUCCES - Tous les tests sont passes!")
        print("OK - Le systeme de charges bailleur est operationnel!")
    else:
        print("ATTENTION - Certains tests ont echoue. Verifiez les erreurs ci-dessus.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)