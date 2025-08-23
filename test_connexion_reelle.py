#!/usr/bin/env python
"""
Test de connexion réelle pour identifier le problème de redirection persistante
- Simulation d'une vraie connexion via le formulaire
- Vérification de la session et de l'authentification
- Test des redirections après connexion
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from utilisateurs.models import Utilisateur, GroupeTravail

def test_connexion_reelle():
    """Test de connexion réelle pour identifier le problème"""
    
    print("🔐 TEST DE CONNEXION RÉELLE")
    print("=" * 50)
    
    # Étape 1: Vérifier l'état initial
    print("\n📋 Étape 1: État initial")
    print("-" * 30)
    
    client = Client()
    
    # Tester l'accès à la page de connexion des groupes
    response = client.get('/utilisateurs/')
    print(f"✅ GET /utilisateurs/ - Status: {response.status_code}")
    
    # Tester l'accès à une page protégée (doit rediriger)
    response = client.get('/paiements/retraits/')
    print(f"✅ GET /paiements/retraits/ (non connecté) - Status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"✅ Redirection vers: {response.url}")
    else:
        print(f"❌ Pas de redirection: {response.status_code}")
    
    # Étape 2: Trouver un utilisateur valide pour la connexion
    print("\n🔍 Étape 2: Recherche d'un utilisateur valide")
    print("-" * 30)
    
    utilisateur_test = None
    for user in Utilisateur.objects.all():
        if user.groupe_travail and user.actif:
            utilisateur_test = user
            break
    
    if not utilisateur_test:
        print("❌ Aucun utilisateur valide trouvé")
        return False
    
    print(f"✅ Utilisateur de test: {utilisateur_test.username}")
    print(f"   Groupe: {utilisateur_test.groupe_travail.nom}")
    print(f"   Actif: {utilisateur_test.actif}")
    
    # Étape 3: Simuler la connexion via le formulaire
    print("\n🔑 Étape 3: Simulation de connexion via formulaire")
    print("-" * 30)
    
    try:
        # Simuler la connexion via le formulaire de connexion des groupes
        response = client.post('/utilisateurs/', {
            'username': utilisateur_test.username,
            'password': 'test123',  # Mot de passe par défaut
        }, follow=True)
        
        print(f"✅ POST /utilisateurs/ - Status: {response.status_code}")
        print(f"   Redirections: {len(response.redirect_chain)}")
        
        for i, (url, status) in enumerate(response.redirect_chain):
            print(f"   Redirection {i+1}: {status} -> {url}")
        
        # Vérifier si l'utilisateur est connecté
        if response.context and 'user' in response.context:
            user = response.context['user']
            print(f"✅ Utilisateur dans le contexte: {user.username}")
            print(f"   Authentifié: {user.is_authenticated}")
        else:
            print("⚠️ Pas d'utilisateur dans le contexte")
            
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
    
    # Étape 4: Vérifier l'état de la session
    print("\n📱 Étape 4: Vérification de la session")
    print("-" * 30)
    
    try:
        # Vérifier si l'utilisateur est connecté dans la session
        session = client.session
        print(f"✅ Session ID: {session.session_key}")
        
        if 'user_id' in session:
            print(f"✅ User ID dans la session: {session['user_id']}")
        else:
            print("⚠️ Pas de user_id dans la session")
            
        if '_auth_user_id' in session:
            print(f"✅ _auth_user_id dans la session: {session['_auth_user_id']}")
        else:
            print("⚠️ Pas de _auth_user_id dans la session")
            
        if '_auth_user_backend' in session:
            print(f"✅ Backend d'authentification: {session['_auth_user_backend']}")
        else:
            print("⚠️ Pas de backend d'authentification")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la session: {e}")
    
    # Étape 5: Tester l'accès à la page protégée après connexion
    print("\n🌐 Étape 5: Test d'accès après connexion")
    print("-" * 30)
    
    try:
        # Tester l'accès à la page des retraits après connexion
        response = client.get('/paiements/retraits/')
        print(f"✅ GET /paiements/retraits/ (après connexion) - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page accessible après connexion")
        elif response.status_code == 302:
            print(f"⚠️ Redirection après connexion vers: {response.url}")
            
            # Suivre la redirection
            response = client.get(response.url, follow=True)
            print(f"   Suivi de la redirection - Status final: {response.status_code}")
            
        else:
            print(f"❌ Erreur après connexion: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'accès: {e}")
    
    # Étape 6: Vérifier les cookies et l'en-tête d'autorisation
    print("\n🍪 Étape 6: Vérification des cookies et en-têtes")
    print("-" * 30)
    
    try:
        # Vérifier les cookies de session
        cookies = client.cookies
        print(f"✅ Nombre de cookies: {len(cookies)}")
        
        for name, cookie in cookies.items():
            print(f"   Cookie {name}: {cookie.value[:50]}...")
        
        # Vérifier les en-têtes de la dernière réponse
        if hasattr(client, 'response'):
            headers = client.response.headers
            print(f"✅ En-têtes de la réponse:")
            for name, value in headers.items():
                if name.lower() in ['set-cookie', 'authorization', 'x-csrftoken']:
                    print(f"   {name}: {value[:50]}...")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des cookies: {e}")
    
    # Étape 7: Test avec force_login (méthode alternative)
    print("\n⚡ Étape 7: Test avec force_login")
    print("-" * 30)
    
    try:
        # Créer un nouveau client et utiliser force_login
        client2 = Client()
        client2.force_login(utilisateur_test)
        
        # Tester l'accès
        response = client2.get('/paiements/retraits/')
        print(f"✅ GET /paiements/retraits/ (force_login) - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page accessible avec force_login")
        else:
            print(f"❌ Erreur avec force_login: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur avec force_login: {e}")
    
    print("\n✅ TEST TERMINÉ !")
    print("🎯 Analysez les résultats pour identifier le problème de redirection")
    
    return True

if __name__ == "__main__":
    test_connexion_reelle()
