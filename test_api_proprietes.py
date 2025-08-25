#!/usr/bin/env python
"""
Script de test pour vérifier l'API des propriétés et le remplissage automatique du loyer
"""

import os
import sys
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Propriete
from django.contrib.auth import get_user_model

def test_api_proprietes():
    """Test de l'API des propriétés"""
    
    print("🧪 Test de l'API des propriétés")
    print("=" * 50)
    
    try:
        # 1. Vérifier qu'il y a des propriétés dans la base
        proprietes = Propriete.objects.all()
        print(f"\n1. Nombre de propriétés dans la base : {proprietes.count()}")
        
        if proprietes.exists():
            # Prendre la première propriété pour le test
            propriete = proprietes.first()
            print(f"   Propriété de test : {propriete.titre}")
            print(f"   Loyer actuel : {propriete.loyer_actuel}")
            print(f"   ID : {propriete.id}")
            
            # 2. Tester l'API directement
            print(f"\n2. Test de l'API REST...")
            
            # Test avec l'URL de l'API
            api_url = f"http://localhost:8000/proprietes/api/proprietes/{propriete.id}/"
            print(f"   URL de test : {api_url}")
            
            try:
                response = requests.get(api_url, timeout=5)
                print(f"   Statut de la réponse : {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Données reçues : {json.dumps(data, indent=2)}")
                    
                    if 'loyer_actuel' in data:
                        print(f"   ✅ Loyer récupéré via API : {data['loyer_actuel']}")
                    else:
                        print(f"   ❌ Loyer non trouvé dans la réponse API")
                else:
                    print(f"   ❌ Erreur API : {response.status_code}")
                    print(f"   Contenu de la réponse : {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Erreur de connexion à l'API : {e}")
                print(f"   Assurez-vous que le serveur Django fonctionne sur le port 8001")
            
            # 3. Test avec l'URL alternative
            print(f"\n3. Test avec URL alternative...")
            alt_api_url = f"http://localhost:8000/proprietes/api/proprietes/{propriete.id}/"
            print(f"   URL alternative : {alt_api_url}")
            
            try:
                response = requests.get(alt_api_url, timeout=5)
                print(f"   Statut de la réponse : {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Données récupérées via URL alternative")
                    if 'loyer_actuel' in data:
                        print(f"   Loyer : {data['loyer_actuel']}")
                else:
                    print(f"   ❌ Erreur avec URL alternative : {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Erreur de connexion : {e}")
        
        else:
            print("   ❌ Aucune propriété trouvée dans la base de données")
        
        # 4. Vérifier la configuration des URLs
        print(f"\n4. Vérification de la configuration...")
        
        try:
            from proprietes.urls import urlpatterns
            api_urls = [url for url in urlpatterns if 'api' in str(url)]
            print(f"   URLs API trouvées : {len(api_urls)}")
            
            for url in api_urls:
                print(f"   - {url}")
                
        except Exception as e:
            print(f"   ❌ Erreur lors de la vérification des URLs : {e}")
        
        print(f"\n🎯 Recommandations :")
        print(f"   1. Vérifiez que le serveur Django fonctionne sur le port 8001")
        print(f"   2. Vérifiez que l'URL de l'API est correcte dans le JavaScript")
        print(f"   3. Vérifiez les logs du serveur pour d'éventuelles erreurs")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_proprietes()
