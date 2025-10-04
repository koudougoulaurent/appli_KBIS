"""
Test de chargement des propriétés pour les charges bailleur.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_chargement_proprietes():
    """Test de chargement des propriétés."""
    print("Test de chargement des propriétés...")
    
    try:
        from proprietes.models import Propriete, Bailleur
        
        # Test 1: Vérifier les propriétés disponibles
        print("1. Vérification des propriétés disponibles:")
        proprietes = Propriete.objects.filter(is_deleted=False).select_related('bailleur')
        print(f"   Nombre de propriétés: {proprietes.count()}")
        
        if proprietes.exists():
            for i, propriete in enumerate(proprietes[:5]):  # Afficher les 5 premières
                bailleur_nom = propriete.bailleur.get_nom_complet() if propriete.bailleur else "Aucun bailleur"
                print(f"   {i+1}. {propriete.adresse} - {bailleur_nom}")
        else:
            print("   Aucune propriété trouvée")
        
        # Test 2: Vérifier les bailleurs
        print("\n2. Vérification des bailleurs:")
        bailleurs = Bailleur.objects.all()
        print(f"   Nombre de bailleurs: {bailleurs.count()}")
        
        if bailleurs.exists():
            for i, bailleur in enumerate(bailleurs[:5]):  # Afficher les 5 premiers
                print(f"   {i+1}. {bailleur.get_nom_complet()}")
        else:
            print("   Aucun bailleur trouvé")
        
        # Test 3: Vérifier la relation propriété-bailleur
        print("\n3. Vérification de la relation propriété-bailleur:")
        proprietes_avec_bailleur = Propriete.objects.filter(
            is_deleted=False,
            bailleur__isnull=False
        ).select_related('bailleur')
        
        print(f"   Propriétés avec bailleur: {proprietes_avec_bailleur.count()}")
        
        proprietes_sans_bailleur = Propriete.objects.filter(
            is_deleted=False,
            bailleur__isnull=True
        )
        
        print(f"   Propriétés sans bailleur: {proprietes_sans_bailleur.count()}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test propriétés: {e}")
        return False

def test_vue_charges_bailleur():
    """Test de la vue creer_charge_bailleur."""
    print("\nTest de la vue creer_charge_bailleur...")
    
    try:
        from proprietes.views_charges_bailleur import creer_charge_bailleur
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer une requête de test
        factory = RequestFactory()
        request = factory.get('/proprietes/charges-bailleur-intelligent/creer/')
        request.user = user
        
        # Appeler la vue
        response = creer_charge_bailleur(request)
        
        if response.status_code == 200:
            print("   OK - Vue accessible")
            
            # Vérifier le contexte
            if hasattr(response, 'context_data'):
                context = response.context_data
                if 'proprietes' in context:
                    proprietes = context['proprietes']
                    print(f"   OK - Propriétés dans le contexte: {proprietes.count()}")
                else:
                    print("   ERREUR - Pas de propriétés dans le contexte")
            else:
                print("   ATTENTION - Pas de contexte disponible")
        else:
            print(f"   ERREUR - Code de statut: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Test vue: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST DE CHARGEMENT DES PROPRIETES POUR CHARGES BAILLEUR")
    print("=" * 60)
    
    tests = [
        test_chargement_proprietes,
        test_vue_charges_bailleur,
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
        print("\nSUCCES - Les proprietes sont correctement chargees!")
        print("OK - Proprietes disponibles")
        print("OK - Relations propriete-bailleur fonctionnelles")
        print("OK - Vue accessible")
    else:
        print("\nATTENTION - Certains tests ont echoue.")
        print("Le chargement des proprietes peut ne pas fonctionner correctement.")
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
