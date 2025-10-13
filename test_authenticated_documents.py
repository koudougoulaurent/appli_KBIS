#!/usr/bin/env python
"""
Script pour tester la génération de documents avec authentification
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from django.contrib.auth.models import AnonymousUser
from paiements.views_kbis_recus import generer_recu_kbis_dynamique

User = get_user_model()


def test_authenticated_documents():
    """Test la génération de documents avec authentification"""
    print("=== TEST DOCUMENTS AUTHENTIFIES ===\n")
    
    # Test 1: Créer un utilisateur de test
    print("1. Creation utilisateur de test...")
    try:
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'is_staff': True,
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print("   [OK] Utilisateur de test cree")
        else:
            print("   [OK] Utilisateur de test existe deja")
        
        print(f"   Utilisateur: {user.username} (ID: {user.id})")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
        return
    
    print()
    
    # Test 2: Tester la vue avec authentification
    print("2. Test vue avec authentification...")
    try:
        paiement = Paiement.objects.filter(statut='valide').first()
        if not paiement:
            print("   [ERREUR] Aucun paiement valide trouve")
            return
        
        print(f"   Paiement: ID {paiement.id}")
        
        # Créer un client de test
        client = Client()
        
        # Se connecter
        login_success = client.login(username='test_user', password='testpass123')
        print(f"   Connexion: {'OK' if login_success else 'ECHEC'}")
        
        if login_success:
            # Tester la génération de récépissé
            url = f'/paiements/paiement/{paiement.id}/recu-kbis/'
            print(f"   URL: {url}")
            
            response = client.get(url)
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.get('Content-Type', 'Non specifie')}")
            
            if response.status_code == 200:
                print("   [OK] Generation reussie")
                
                # Vérifier le contenu
                content = response.content.decode('utf-8')
                if 'enteteEnImage.png' in content:
                    print("   [OK] Image d'entete presente")
                else:
                    print("   [ATTENTION] Image d'entete manquante")
                
                # Sauvegarder pour inspection
                with open('test_authenticated_recu.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("   Fichier sauvegarde: test_authenticated_recu.html")
            else:
                print(f"   [ATTENTION] Status inattendu: {response.status_code}")
                print(f"   Contenu (premiers 200 caracteres): {response.content.decode('utf-8')[:200]}")
        else:
            print("   [ERREUR] Impossible de se connecter")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Tester avec RequestFactory
    print("3. Test avec RequestFactory...")
    try:
        factory = RequestFactory()
        request = factory.get(f'/paiements/paiement/{paiement.id}/recu-kbis/')
        request.user = user
        
        # Simuler la vue directement
        response = generer_recu_kbis_dynamique(request, paiement.id)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.get('Content-Type', 'Non specifie')}")
        
        if response.status_code == 200:
            print("   [OK] Generation reussie avec RequestFactory")
            
            # Vérifier le contenu
            content = response.content.decode('utf-8')
            if 'enteteEnImage.png' in content:
                print("   [OK] Image d'entete presente")
            else:
                print("   [ATTENTION] Image d'entete manquante")
            
            # Sauvegarder pour inspection
            with open('test_factory_recu.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("   Fichier sauvegarde: test_factory_recu.html")
        else:
            print(f"   [ATTENTION] Status inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== FIN TESTS AUTHENTIFIES ===")


if __name__ == "__main__":
    test_authenticated_documents()

