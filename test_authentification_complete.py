#!/usr/bin/env python
"""
Test de l'authentification complète
- Sélection du groupe de travail
- Connexion sur la page spécifique du groupe
- Vérification de l'accès aux pages protégées
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from utilisateurs.models import Utilisateur, GroupeTravail

def test_authentification_complete():
    """Test de l'authentification complète"""
    
    print("🔐 TEST DE L'AUTHENTIFICATION COMPLÈTE")
    print("=" * 60)
    
    # Étape 1: Vérifier l'état initial
    print("\n📋 Étape 1: État initial")
    print("-" * 40)
    
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
    print("-" * 40)
    
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
    
    # Étape 3: Sélectionner le groupe de travail
    print("\n🏢 Étape 3: Sélection du groupe de travail")
    print("-" * 40)
    
    try:
        # Simuler la sélection du groupe
        groupe_nom = utilisateur_test.groupe_travail.nom
        response = client.post('/utilisateurs/', {
            'groupe': groupe_nom
        }, follow=True)
        
        print(f"✅ POST /utilisateurs/ (sélection groupe) - Status: {response.status_code}")
        print(f"   Redirections: {len(response.redirect_chain)}")
        
        for i, (url, status) in enumerate(response.redirect_chain):
            print(f"   Redirection {i+1}: {status} -> {url}")
        
        # Vérifier que nous sommes sur la page de connexion du groupe
        if 'login_groupe' in str(response.url):
            print("✅ Redirection vers la page de connexion du groupe")
        else:
            print(f"⚠️ Redirection inattendue vers: {response.url}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la sélection du groupe: {e}")
    
    # Étape 4: Connexion sur la page du groupe
    print("\n🔑 Étape 4: Connexion sur la page du groupe")
    print("-" * 40)
    
    try:
        # Construire l'URL de connexion du groupe
        groupe_nom = utilisateur_test.groupe_travail.nom
        login_url = f'/utilisateurs/login/{groupe_nom}/'
        
        print(f"✅ URL de connexion: {login_url}")
        
        # Simuler la connexion sur la page du groupe
        response = client.post(login_url, {
            'username': utilisateur_test.username,
            'password': 'test123',  # Mot de passe par défaut
        }, follow=True)
        
        print(f"✅ POST {login_url} - Status: {response.status_code}")
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
    
    # Étape 5: Vérifier l'état de la session
    print("\n📱 Étape 5: Vérification de la session")
    print("-" * 40)
    
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
            
        # Vérifier le groupe sélectionné
        if 'groupe_selectionne' in session:
            print(f"✅ Groupe sélectionné: {session['groupe_selectionne']}")
        else:
            print("⚠️ Pas de groupe sélectionné dans la session")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la session: {e}")
    
    # Étape 6: Tester l'accès à la page protégée après connexion
    print("\n🌐 Étape 6: Test d'accès après connexion")
    print("-" * 40)
    
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
    
    # Étape 7: Test avec force_login pour comparaison
    print("\n⚡ Étape 7: Test avec force_login pour comparaison")
    print("-" * 40)
    
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
    test_authentification_complete()
