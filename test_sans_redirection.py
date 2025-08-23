#!/usr/bin/env python
"""
Test rapide pour vérifier que la redirection est désactivée
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client

def test_sans_redirection():
    """Test que la redirection est désactivée"""
    
    print("🧪 TEST SANS REDIRECTION")
    print("=" * 40)
    
    client = Client()
    
    # Tester l'accès à la page des retraits
    response = client.get('/paiements/retraits/')
    print(f"✅ GET /paiements/retraits/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("🎉 SUCCÈS ! Page accessible sans redirection")
        print("✅ La redirection forcée est désactivée !")
        return True
    elif response.status_code == 302:
        print(f"⚠️ Redirection toujours active vers: {response.url}")
        return False
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False

if __name__ == "__main__":
    test_sans_redirection()
