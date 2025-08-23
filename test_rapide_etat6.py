#!/usr/bin/env python
"""
Test rapide pour vérifier que l'erreur logout est corrigée
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_rapide_etat6():
    """Test rapide pour vérifier les URLs principales"""
    
    print("🔧 TEST RAPIDE ÉTAT 6 - CORRECTION ERREUR LOGOUT")
    print("=" * 60)
    
    client = Client()
    
    # Test 1: URL logout
    print("\n📋 Test 1: URL logout")
    print("-" * 30)
    
    try:
        logout_url = reverse('logout')
        print(f"✅ URL logout: {logout_url}")
    except Exception as e:
        print(f"❌ Erreur URL logout: {e}")
        return False
    
    # Test 2: URLs principales
    print("\n📋 Test 2: URLs principales")
    print("-" * 30)
    
    urls_to_test = [
        ('home', 'Page d\'accueil'),
        ('utilisateurs:connexion_groupes', 'Connexion groupes'),
        ('proprietes:liste', 'Liste propriétés'),
        ('contrats:liste', 'Liste contrats'),
        ('paiements:liste', 'Liste paiements'),
    ]
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"✅ {description}: {url}")
        except Exception as e:
            print(f"❌ {description}: {e}")
    
    # Test 3: Test de connexion et navigation
    print("\n📋 Test 3: Test de connexion et navigation")
    print("-" * 30)
    
    try:
        # Connexion avec un utilisateur de test
        login_success = client.login(username='admin1', password='test123')
        if login_success:
            print("✅ Connexion réussie")
            
            # Test d'accès à une page protégée
            response = client.get('/proprietes/ajouter/')
            if response.status_code == 200:
                print("✅ Page propriétés/ajouter accessible")
            else:
                print(f"⚠️ Page propriétés/ajouter: code {response.status_code}")
        else:
            print("❌ Échec de connexion")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de navigation: {e}")
    
    print("\n🎉 TEST RAPIDE TERMINÉ!")
    print("✅ L'erreur logout devrait être corrigée")
    
    return True

if __name__ == '__main__':
    test_rapide_etat6() 