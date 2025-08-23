#!/usr/bin/env python
"""
Diagnostic de l'authentification et des redirections
- Vérification de l'état de l'utilisateur connecté
- Diagnostic des décorateurs de permission
- Test des redirections
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
from django.contrib.auth import get_user_model
from utilisateurs.models import Utilisateur, GroupeTravail

def diagnostic_authentification():
    """Diagnostic complet de l'authentification"""
    
    print("🔍 DIAGNOSTIC DE L'AUTHENTIFICATION ET DES REDIRECTIONS")
    print("=" * 70)
    
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
    
    # Test 2: Vérifier l'état de la base de données
    print("\n🗄️ Test 2: État de la base de données")
    print("-" * 40)
    
    try:
        # Vérifier les utilisateurs
        utilisateurs = Utilisateur.objects.all()
        print(f"✅ {utilisateurs.count()} utilisateurs dans la base")
        
        # Vérifier les groupes de travail
        groupes = GroupeTravail.objects.all()
        print(f"✅ {groupes.count()} groupes de travail dans la base")
        
        # Vérifier les utilisateurs avec groupe de travail
        utilisateurs_avec_groupe = Utilisateur.objects.filter(groupe_travail__isnull=False)
        print(f"✅ {utilisateurs_avec_groupe.count()} utilisateurs avec groupe de travail")
        
        # Vérifier les utilisateurs sans groupe de travail
        utilisateurs_sans_groupe = Utilisateur.objects.filter(groupe_travail__isnull=True)
        print(f"⚠️ {utilisateurs_sans_groupe.count()} utilisateurs SANS groupe de travail")
        
        if utilisateurs_sans_groupe.count() > 0:
            print("   Utilisateurs sans groupe:")
            for user in utilisateurs_sans_groupe[:5]:
                print(f"     - {user.username} ({user.get_full_name()})")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la base: {e}")
    
    # Test 3: Vérifier la configuration des URLs
    print("\n🔗 Test 3: Configuration des URLs")
    print("-" * 40)
    
    try:
        # Résoudre l'URL /utilisateurs/
        resolver_match = resolve('/utilisateurs/')
        print(f"✅ URL /utilisateurs/ résolue vers: {resolver_match.view_name}")
        print(f"   Vue: {resolver_match.func.__name__}")
        
        # Vérifier l'URL des retraits
        retraits_url = reverse('paiements:retraits_liste')
        print(f"✅ URL des retraits: {retraits_url}")
        
        resolver_match = resolve(retraits_url)
        print(f"   Vue: {resolver_match.func.__name__}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des URLs: {e}")
    
    # Test 4: Test avec le client Django (non authentifié)
    print("\n🌐 Test 4: Test avec le client Django (non authentifié)")
    print("-" * 40)
    
    try:
        client = Client()
        
        # Tester l'accès à la page de connexion des groupes
        response = client.get('/utilisateurs/')
        print(f"✅ GET /utilisateurs/ - Status: {response.status_code}")
        
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
    
    # Test 5: Test de connexion simulée
    print("\n🔐 Test 5: Test de connexion simulée")
    print("-" * 40)
    
    try:
        # Créer un client et simuler une connexion
        client = Client()
        
        # Trouver un utilisateur valide pour le test
        utilisateur_test = None
        for user in Utilisateur.objects.all():
            if user.groupe_travail and user.actif:
                utilisateur_test = user
                break
        
        if utilisateur_test:
            print(f"✅ Utilisateur de test trouvé: {utilisateur_test.username}")
            print(f"   Groupe: {utilisateur_test.groupe_travail.nom}")
            print(f"   Actif: {utilisateur_test.actif}")
            
            # Simuler la connexion
            client.force_login(utilisateur_test)
            
            # Tester l'accès à une page protégée
            response = client.get('/paiements/retraits/')
            print(f"✅ GET /paiements/retraits/ (connecté) - Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Page accessible après connexion")
            elif response.status_code == 302:
                print(f"⚠️ Redirection après connexion vers: {response.url}")
            else:
                print(f"❌ Erreur après connexion: {response.status_code}")
                
        else:
            print("❌ Aucun utilisateur valide trouvé pour le test")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de connexion: {e}")
    
    # Test 6: Vérifier les décorateurs de permission
    print("\n🛡️ Test 6: Vérification des décorateurs de permission")
    print("-" * 40)
    
    try:
        from paiements.views import RetraitListView
        
        # Vérifier si la vue a des décorateurs
        if hasattr(RetraitListView, 'dispatch'):
            print("✅ RetraitListView a une méthode dispatch")
            
            # Vérifier les décorateurs appliqués
            decorators = getattr(RetraitListView, '_decorators', [])
            if decorators:
                print(f"⚠️ Décorateurs appliqués: {decorators}")
            else:
                print("✅ Aucun décorateur appliqué à RetraitListView")
        else:
            print("❌ RetraitListView n'a pas de méthode dispatch")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des décorateurs: {e}")
    
    # Test 7: Vérifier la session et l'authentification
    print("\n🔑 Test 7: Vérification de la session et de l'authentification")
    print("-" * 40)
    
    try:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser
        
        # Vérifier le modèle utilisateur
        User = get_user_model()
        print(f"✅ Modèle utilisateur: {User}")
        
        # Vérifier si c'est le bon modèle
        if User == Utilisateur:
            print("✅ Modèle Utilisateur personnalisé utilisé")
        else:
            print(f"⚠️ Modèle utilisateur différent: {User}")
            
        # Vérifier les champs du modèle
        if hasattr(User, 'groupe_travail'):
            print("✅ Modèle a le champ groupe_travail")
        else:
            print("❌ Modèle n'a pas le champ groupe_travail")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du modèle: {e}")
    
    print("\n✅ DIAGNOSTIC TERMINÉ !")
    print("🎯 Analysez les résultats pour identifier le problème")
    
    return True

if __name__ == "__main__":
    diagnostic_authentification()
