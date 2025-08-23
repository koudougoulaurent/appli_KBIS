#!/usr/bin/env python
"""
Test de correction pour l'état 7 - Vérification des URLs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import authenticate

def test_correction_etat7():
    """Test des corrections de l'état 7"""
    
    print("🔧 TEST CORRECTION ÉTAT 7 - VÉRIFICATION DES URLS")
    print("=" * 60)
    
    client = Client()
    
    # Test 1: URLs utilisateurs
    print("\n📋 Test 1: URLs utilisateurs")
    print("-" * 30)
    
    try:
        # Test URL ajouter_utilisateur
        ajouter_url = reverse('utilisateurs:ajouter_utilisateur')
        print(f"✅ URL ajouter_utilisateur: {ajouter_url}")
    except Exception as e:
        print(f"❌ Erreur URL ajouter_utilisateur: {e}")
        return False
    
    try:
        # Test URL detail_utilisateur
        detail_url = reverse('utilisateurs:detail_utilisateur', args=[1])
        print(f"✅ URL detail_utilisateur: {detail_url}")
    except Exception as e:
        print(f"❌ Erreur URL detail_utilisateur: {e}")
        return False
    
    try:
        # Test URL modifier_utilisateur
        modifier_url = reverse('utilisateurs:modifier_utilisateur', args=[1])
        print(f"✅ URL modifier_utilisateur: {modifier_url}")
    except Exception as e:
        print(f"❌ Erreur URL modifier_utilisateur: {e}")
        return False
    
    # Test 2: Accès aux pages
    print("\n🌐 Test 2: Accès aux pages")
    print("-" * 30)
    
    # Connexion avec un utilisateur de test
    user = authenticate(username='privilege1', password='test123')
    if user:
        client.force_login(user)
        print("✅ Connexion réussie avec privilege1")
        
        # Test page liste utilisateurs
        try:
            response = client.get('/utilisateurs/utilisateurs/')
            if response.status_code == 200:
                print("✅ Page liste utilisateurs accessible")
            else:
                print(f"❌ Erreur page liste utilisateurs: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur accès liste utilisateurs: {e}")
            return False
        
        # Test page ajouter utilisateur
        try:
            response = client.get('/utilisateurs/utilisateurs/ajouter/')
            if response.status_code == 200:
                print("✅ Page ajouter utilisateur accessible")
            else:
                print(f"❌ Erreur page ajouter utilisateur: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur accès ajouter utilisateur: {e}")
            return False
        
    else:
        print("❌ Impossible de se connecter avec privilege1")
        return False
    
    # Test 3: URLs principales
    print("\n🔗 Test 3: URLs principales")
    print("-" * 30)
    
    try:
        logout_url = reverse('logout')
        print(f"✅ URL logout: {logout_url}")
    except Exception as e:
        print(f"❌ Erreur URL logout: {e}")
        return False
    
    try:
        liste_url = reverse('utilisateurs:liste_utilisateurs')
        print(f"✅ URL liste_utilisateurs: {liste_url}")
    except Exception as e:
        print(f"❌ Erreur URL liste_utilisateurs: {e}")
        return False
    
    print("\n✅ TOUS LES TESTS PASSÉS !")
    print("🎉 L'état 7 est maintenant complètement corrigé !")
    
    return True

if __name__ == "__main__":
    test_correction_etat7() 