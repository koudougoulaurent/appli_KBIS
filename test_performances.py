#!/usr/bin/env python
"""
Test des performances de l'application
"""

import os
import sys
import django
import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail

def test_performances():
    """Test des performances de l'application"""
    
    print("⚡ TEST DES PERFORMANCES")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Temps de connexion
    print("\n🔐 Test 1: Temps de connexion")
    print("-" * 30)
    
    start_time = time.time()
    
    # Connexion avec un utilisateur privilégié
    user = authenticate(username='privilege1', password='test123')
    if user:
        client.force_login(user)
        login_time = time.time() - start_time
        print(f"✅ Connexion réussie en {login_time:.3f} secondes")
    else:
        print("❌ Échec de la connexion")
        return False
    
    # Test 2: Temps de chargement de la page de connexion des groupes
    print("\n🌐 Test 2: Page de connexion des groupes")
    print("-" * 30)
    
    start_time = time.time()
    try:
        response = client.get('/utilisateurs/')
        load_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Page chargée en {load_time:.3f} secondes")
        else:
            print(f"❌ Erreur page connexion: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur accès page connexion: {e}")
        return False
    
    # Test 3: Temps de connexion au groupe
    print("\n🔐 Test 3: Connexion au groupe PRIVILEGE")
    print("-" * 30)
    
    start_time = time.time()
    try:
        response = client.post('/utilisateurs/', {'groupe': 'PRIVILEGE'})
        group_login_time = time.time() - start_time
        if response.status_code == 302:  # Redirection
            print(f"✅ Connexion groupe en {group_login_time:.3f} secondes")
        else:
            print(f"❌ Erreur connexion groupe: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion groupe: {e}")
        return False
    
    # Test 4: Temps de chargement du dashboard
    print("\n📊 Test 4: Dashboard PRIVILEGE")
    print("-" * 30)
    
    start_time = time.time()
    try:
        response = client.get('/utilisateurs/dashboard/PRIVILEGE/')
        dashboard_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Dashboard chargé en {dashboard_time:.3f} secondes")
        else:
            print(f"❌ Erreur dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur dashboard: {e}")
        return False
    
    # Test 5: Temps de chargement de la liste des utilisateurs
    print("\n📋 Test 5: Liste des utilisateurs")
    print("-" * 30)
    
    start_time = time.time()
    try:
        response = client.get('/utilisateurs/utilisateurs/')
        liste_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Liste chargée en {liste_time:.3f} secondes")
        else:
            print(f"❌ Erreur liste: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur liste: {e}")
        return False
    
    # Test 6: Temps de chargement de la page d'ajout d'utilisateur
    print("\n➕ Test 6: Page d'ajout d'utilisateur")
    print("-" * 30)
    
    start_time = time.time()
    try:
        response = client.get('/utilisateurs/utilisateurs/ajouter/')
        ajout_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Page ajout chargée en {ajout_time:.3f} secondes")
        else:
            print(f"❌ Erreur page ajout: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur page ajout: {e}")
        return False
    
    # Test 7: Temps de chargement des autres pages
    print("\n📄 Test 7: Autres pages")
    print("-" * 30)
    
    pages_to_test = [
        ('/proprietes/', 'Liste propriétés'),
        ('/contrats/liste/', 'Liste contrats'),
        ('/paiements/liste/', 'Liste paiements'),
    ]
    
    for url, name in pages_to_test:
        start_time = time.time()
        try:
            response = client.get(url)
            page_time = time.time() - start_time
            if response.status_code == 200:
                print(f"✅ {name} chargée en {page_time:.3f} secondes")
            else:
                print(f"❌ Erreur {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur {name}: {e}")
    
    # Test 8: Analyse des performances
    print("\n📊 Test 8: Analyse des performances")
    print("-" * 30)
    
    total_time = login_time + load_time + group_login_time + dashboard_time + liste_time + ajout_time
    print(f"⏱️ Temps total: {total_time:.3f} secondes")
    
    if total_time < 2.0:
        print("✅ Excellentes performances !")
    elif total_time < 5.0:
        print("✅ Bonnes performances")
    elif total_time < 10.0:
        print("⚠️ Performances acceptables")
    else:
        print("❌ Performances lentes - optimisation nécessaire")
    
    # Test 9: Optimisations recommandées
    print("\n🔧 Test 9: Recommandations d'optimisation")
    print("-" * 30)
    
    if dashboard_time > 1.0:
        print("💡 Optimisation dashboard: Utiliser le cache pour les statistiques")
    
    if liste_time > 0.5:
        print("💡 Optimisation liste: Pagination et select_related")
    
    if total_time > 5.0:
        print("💡 Optimisation générale: Mise en cache des requêtes fréquentes")
    
    print("\n✅ Test des performances terminé !")
    
    return True

if __name__ == "__main__":
    test_performances() 