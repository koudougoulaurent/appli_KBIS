#!/usr/bin/env python
"""
Test des corrections des URLs et de la redirection
- Vérification que LOGIN_URL pointe vers la bonne page
- Test des URLs des retraits
- Vérification de la redirection vers la page de connexion des groupes
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse, resolve
from django.conf import settings

def test_urls_corrections():
    """Test des corrections des URLs et de la redirection"""
    
    print("🔍 TEST DES CORRECTIONS DES URLS ET REDIRECTIONS")
    print("=" * 60)
    
    # Test 1: Vérifier la configuration LOGIN_URL
    print("\n📋 Test 1: Configuration LOGIN_URL")
    print("-" * 40)
    
    if hasattr(settings, 'LOGIN_URL'):
        print(f"✅ LOGIN_URL configuré: {settings.LOGIN_URL}")
        
        # Vérifier que l'URL pointe vers la bonne page
        if settings.LOGIN_URL == '/utilisateurs/':
            print("✅ LOGIN_URL pointe vers la page de connexion des groupes")
        else:
            print(f"❌ LOGIN_URL incorrect: {settings.LOGIN_URL}")
    else:
        print("❌ LOGIN_URL non configuré")
    
    # Test 2: Vérifier que l'URL /utilisateurs/ fonctionne
    print("\n🔗 Test 2: URL /utilisateurs/")
    print("-" * 40)
    
    try:
        # Résoudre l'URL /utilisateurs/
        resolver_match = resolve('/utilisateurs/')
        print(f"✅ URL /utilisateurs/ résolue vers: {resolver_match.view_name}")
        print(f"   Vue: {resolver_match.func.__name__}")
        print(f"   Arguments: {resolver_match.kwargs}")
        
        if resolver_match.view_name == 'utilisateurs:connexion_groupes':
            print("✅ URL pointe vers la bonne vue: connexion_groupes")
        else:
            print(f"❌ URL pointe vers la mauvaise vue: {resolver_match.view_name}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la résolution de /utilisateurs/: {e}")
    
    # Test 3: Vérifier que l'URL /utilisateurs/connexion_groupes/ n'existe pas
    print("\n🚫 Test 3: URL /utilisateurs/connexion_groupes/ (ne doit pas exister)")
    print("-" * 40)
    
    try:
        resolver_match = resolve('/utilisateurs/connexion_groupes/')
        print(f"❌ URL /utilisateurs/connexion_groupes/ existe et pointe vers: {resolver_match.view_name}")
    except:
        print("✅ URL /utilisateurs/connexion_groupes/ n'existe pas (comme attendu)")
    
    # Test 4: Vérifier les URLs des retraits
    print("\n💰 Test 4: URLs des retraits")
    print("-" * 40)
    
    try:
        # Vérifier l'URL des retraits
        retraits_url = reverse('paiements:retraits_liste')
        print(f"✅ URL des retraits: {retraits_url}")
        
        # Résoudre l'URL des retraits
        resolver_match = resolve(retraits_url)
        print(f"   Vue: {resolver_match.func.__name__}")
        
        # Vérifier que c'est bien la vue RetraitListView
        if 'RetraitListView' in str(resolver_match.func):
            print("✅ URL pointe vers RetraitListView")
        else:
            print(f"❌ URL ne pointe pas vers RetraitListView: {resolver_match.func}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des URLs des retraits: {e}")
    
    # Test 5: Vérifier que l'URL des retraits bailleurs existe toujours
    print("\n🏦 Test 5: URL des retraits bailleurs")
    print("-" * 40)
    
    try:
        retraits_bailleur_url = reverse('paiements:liste_retraits_bailleur')
        print(f"✅ URL des retraits bailleurs: {retraits_bailleur_url}")
        
        # Résoudre l'URL
        resolver_match = resolve(retraits_bailleur_url)
        print(f"   Vue: {resolver_match.func.__name__}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des URLs des retraits bailleurs: {e}")
    
    # Test 6: Test avec le client Django
    print("\n🌐 Test 6: Test avec le client Django")
    print("-" * 40)
    
    try:
        client = Client()
        
        # Tester l'accès à la page de connexion des groupes
        response = client.get('/utilisateurs/')
        print(f"✅ GET /utilisateurs/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page de connexion des groupes accessible")
        else:
            print(f"❌ Page de connexion des groupes non accessible: {response.status_code}")
            
        # Tester l'accès à une page protégée (doit rediriger)
        response = client.get('/paiements/retraits/')
        print(f"✅ GET /paiements/retraits/ - Status: {response.status_code}")
        
        if response.status_code == 302:  # Redirection
            print(f"✅ Redirection vers: {response.url}")
            if 'utilisateurs' in response.url:
                print("✅ Redirection vers la page de connexion des groupes")
            else:
                print(f"❌ Redirection incorrecte vers: {response.url}")
        else:
            print(f"❌ Pas de redirection: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test avec le client Django: {e}")
    
    # Test 7: Vérifier la configuration des URLs principales
    print("\n⚙️ Test 7: Configuration des URLs principales")
    print("-" * 40)
    
    try:
        from gestion_immobiliere.urls import urlpatterns
        
        # Vérifier que l'URL racine pointe vers core
        root_pattern = None
        for pattern in urlpatterns:
            if pattern.pattern == '':
                root_pattern = pattern
                break
        
        if root_pattern:
            print(f"✅ URL racine configurée: {root_pattern}")
            if 'core.urls' in str(root_pattern):
                print("✅ URL racine pointe vers core.urls")
            else:
                print(f"❌ URL racine ne pointe pas vers core.urls: {root_pattern}")
        else:
            print("❌ URL racine non configurée")
            
        # Vérifier que l'URL utilisateurs est incluse
        utilisateurs_pattern = None
        for pattern in urlpatterns:
            if pattern.pattern == 'utilisateurs/':
                utilisateurs_pattern = pattern
                break
        
        if utilisateurs_pattern:
            print(f"✅ URL utilisateurs configurée: {utilisateurs_pattern}")
            if 'utilisateurs.urls' in str(utilisateurs_pattern):
                print("✅ URL utilisateurs pointe vers utilisateurs.urls")
            else:
                print(f"❌ URL utilisateurs ne pointe pas vers utilisateurs.urls: {utilisateurs_pattern}")
        else:
            print("❌ URL utilisateurs non configurée")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des URLs principales: {e}")
    
    print("\n✅ TOUS LES TESTS TERMINÉS !")
    print("🎉 Vérifiez les résultats ci-dessus pour confirmer les corrections")
    
    return True

if __name__ == "__main__":
    test_urls_corrections()
