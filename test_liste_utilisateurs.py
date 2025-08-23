#!/usr/bin/env python
"""
Test de la liste d'utilisateurs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail

def test_liste_utilisateurs():
    """Test de l'affichage de la liste d'utilisateurs"""
    
    print("🔍 TEST LISTE D'UTILISATEURS")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Connexion avec un utilisateur privilégié
    print("\n👤 Test 1: Connexion utilisateur")
    print("-" * 30)
    
    user = authenticate(username='privilege1', password='test123')
    if user:
        client.force_login(user)
        print("✅ Connexion réussie avec privilege1")
    else:
        print("❌ Échec de la connexion")
        return False
    
    # Test 2: Accès à la page de connexion des groupes
    print("\n🌐 Test 2: Page de connexion des groupes")
    print("-" * 30)
    
    try:
        response = client.get('/utilisateurs/')
        if response.status_code == 200:
            print("✅ Page de connexion des groupes accessible")
        else:
            print(f"❌ Erreur page connexion: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur accès page connexion: {e}")
        return False
    
    # Test 3: Connexion au groupe PRIVILEGE
    print("\n🔐 Test 3: Connexion au groupe PRIVILEGE")
    print("-" * 30)
    
    try:
        response = client.post('/utilisateurs/', {'groupe': 'PRIVILEGE'})
        if response.status_code == 302:  # Redirection
            print("✅ Connexion au groupe PRIVILEGE réussie")
        else:
            print(f"❌ Erreur connexion groupe: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion groupe: {e}")
        return False
    
    # Test 4: Accès au dashboard PRIVILEGE
    print("\n📊 Test 4: Dashboard PRIVILEGE")
    print("-" * 30)
    
    try:
        response = client.get('/utilisateurs/dashboard/PRIVILEGE/')
        if response.status_code == 200:
            print("✅ Dashboard PRIVILEGE accessible")
        else:
            print(f"❌ Erreur dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur dashboard: {e}")
        return False
    
    # Test 5: Accès à la liste des utilisateurs
    print("\n📋 Test 5: Liste des utilisateurs")
    print("-" * 30)
    
    try:
        response = client.get('/utilisateurs/utilisateurs/')
        if response.status_code == 200:
            print("✅ Liste des utilisateurs accessible")
            
            # Vérifier que le contenu contient des utilisateurs
            content = response.content.decode()
            if 'utilisateurs' in content.lower():
                print("✅ Contenu de la liste d'utilisateurs présent")
            else:
                print("⚠️ Contenu de la liste d'utilisateurs manquant")
                
        else:
            print(f"❌ Erreur liste utilisateurs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur liste utilisateurs: {e}")
        return False
    
    # Test 6: Vérifier les données dans la vue
    print("\n🔍 Test 6: Données dans la vue")
    print("-" * 30)
    
    from utilisateurs.views import liste_utilisateurs
    from django.contrib.auth.models import AnonymousUser
    
    # Créer une requête simulée
    request = type('Request', (), {
        'user': user,
        'GET': {},
        'method': 'GET'
    })()
    
    try:
        # Appeler la vue directement
        response = liste_utilisateurs(request)
        if response.status_code == 200:
            print("✅ Vue liste_utilisateurs fonctionne")
            
            # Vérifier le contexte
            context = response.context_data
            if 'utilisateurs' in context:
                utilisateurs_count = context['utilisateurs'].count()
                print(f"✅ {utilisateurs_count} utilisateurs dans le contexte")
            else:
                print("❌ Utilisateurs manquants dans le contexte")
                
        else:
            print(f"❌ Erreur vue liste_utilisateurs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur vue liste_utilisateurs: {e}")
        return False
    
    # Test 7: Vérifier le template
    print("\n📄 Test 7: Template liste.html")
    print("-" * 30)
    
    try:
        from django.template.loader import get_template
        template = get_template('utilisateurs/liste.html')
        print("✅ Template utilisateurs/liste.html trouvé")
        
        # Vérifier que le template peut être rendu
        context = {
            'utilisateurs': Utilisateur.objects.all(),
            'stats': {
                'total': Utilisateur.objects.count(),
                'actifs': Utilisateur.objects.filter(actif=True).count(),
                'inactifs': Utilisateur.objects.filter(actif=False).count(),
            },
            'groupes': GroupeTravail.objects.all(),
        }
        
        rendered = template.render(context)
        if 'utilisateurs' in rendered.lower():
            print("✅ Template rendu avec succès")
        else:
            print("⚠️ Template rendu mais contenu manquant")
            
    except Exception as e:
        print(f"❌ Erreur template: {e}")
        return False
    
    print("\n✅ TOUS LES TESTS PASSÉS !")
    print("🎉 La liste d'utilisateurs fonctionne correctement !")
    
    return True

if __name__ == "__main__":
    test_liste_utilisateurs() 