#!/usr/bin/env python
"""
Test final pour vérifier que toutes les redirections sont désactivées
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client

def test_final_sans_redirection():
    """Test final que toutes les redirections sont désactivées"""
    
    print("🧪 TEST FINAL SANS REDIRECTION")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Page des retraits
    print("\n📋 Test 1: Page des retraits")
    print("-" * 30)
    
    response = client.get('/paiements/retraits/')
    print(f"✅ GET /paiements/retraits/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page accessible sans redirection")
    elif response.status_code == 302:
        print(f"❌ Redirection vers: {response.url}")
    else:
        print(f"❌ Erreur: {response.status_code}")
    
    # Test 2: Page des recaps mensuels
    print("\n📊 Test 2: Page des recaps mensuels")
    print("-" * 30)
    
    response = client.get('/paiements/recaps-mensuels/')
    print(f"✅ GET /paiements/recaps-mensuels/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page accessible sans redirection")
    elif response.status_code == 302:
        print(f"❌ Redirection vers: {response.url}")
    else:
        print(f"❌ Erreur: {response.status_code}")
    
    # Test 3: Page des paiements
    print("\n💰 Test 3: Page des paiements")
    print("-" * 30)
    
    response = client.get('/paiements/')
    print(f"✅ GET /paiements/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page accessible sans redirection")
    elif response.status_code == 302:
        print(f"❌ Redirection vers: {response.url}")
    else:
        print(f"❌ Erreur: {response.status_code}")
    
    # Test 4: Page des recus
    print("\n🧾 Test 4: Page des reçus")
    print("-" * 30)
    
    response = client.get('/paiements/recus/')
    print(f"✅ GET /paiements/recus/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page accessible sans redirection")
    elif response.status_code == 302:
        print(f"❌ Redirection vers: {response.url}")
    else:
        print(f"❌ Erreur: {response.status_code}")
    
    print("\n✅ TEST FINAL TERMINÉ !")
    print("🎯 Vérifiez que toutes les pages sont accessibles sans redirection")
    
    return True

if __name__ == "__main__":
    test_final_sans_redirection()
