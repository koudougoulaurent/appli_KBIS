#!/usr/bin/env python
"""
Script de test pour vérifier que les URLs fonctionnent correctement
"""

import os
import sys
import django
import requests
import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
django.setup()

def test_urls():
    """Test des URLs pour vérifier qu'elles fonctionnent."""
    
    print("Test des URLs corrigees...")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # URLs a tester
    urls_to_test = [
        "/api/dashboard-stats/",
        "/core/api/dashboard-stats/",
        "/favicon.ico",
        "/static/favicon.ico",
        "/dashboard/",
    ]
    
    print("Attente du demarrage du serveur...")
    time.sleep(3)
    
    for url in urls_to_test:
        try:
            full_url = base_url + url
            print(f"\nTest de: {full_url}")
            
            response = requests.get(full_url, timeout=5)
            
            if response.status_code == 200:
                print(f"SUCCES - Code: {response.status_code}")
                if 'application/json' in response.headers.get('content-type', ''):
                    print(f"   Donnees JSON recues: {len(response.text)} caracteres")
                else:
                    print(f"   Contenu recu: {len(response.text)} caracteres")
            elif response.status_code == 404:
                print(f"ERREUR 404 - URL non trouvee")
            else:
                print(f"CODE: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"CONNEXION REFUSEE - Serveur non demarre")
        except requests.exceptions.Timeout:
            print(f"TIMEOUT - Serveur trop lent")
        except Exception as e:
            print(f"ERREUR: {str(e)}")
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    print("Si vous voyez des SUCCES, les corrections fonctionnent")
    print("Si vous voyez des ERREURS 404, il y a encore des problemes")
    print("Verifiez que le serveur est bien demarre sur le port 8000")

if __name__ == "__main__":
    test_urls()
