#!/usr/bin/env python
"""
Test simple de l'API de recherche intelligente
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_api_recherche():
    """Test de l'API de recherche intelligente"""
    
    print("🧪 TEST DE L'API DE RECHERCHE INTELLIGENTE")
    print("=" * 50)
    
    # Récupérer un utilisateur
    User = get_user_model()
    user = User.objects.first()
    print(f"✅ Utilisateur: {user.username}")
    
    # Tester l'API
    client = Client()
    client.force_login(user)
    
    print(f"\n🔍 TEST DE L'API DE RECHERCHE")
    print("-" * 40)
    
    # Test de l'API de recherche
    try:
        response = client.get('/paiements/api/recherche-rapide/?q=CTN')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API accessible !")
            print(f"   Résultats: {len(data.get('resultats', []))}")
            
            if data.get('resultats'):
                for resultat in data['resultats'][:3]:  # Afficher les 3 premiers
                    print(f"      - {resultat.get('numero_contrat')} - {resultat.get('locataire_nom')}")
            else:
                print(f"      Aucun résultat trouvé pour 'CTN'")
                
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Contenu: {response.content}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")
    
    print(f"\n🧠 TEST DE L'API DE CONTEXTE")
    print("-" * 40)
    
    # Test de l'API de contexte
    try:
        response = client.get('/paiements/api/contexte-intelligent/contrat/1/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API de contexte accessible !")
            print(f"   Contrat: {data.get('contrat', {}).get('numero', 'N/A')}")
            print(f"   Locataire: {data.get('locataire', {}).get('nom_complet', 'N/A')}")
            print(f"   Paiements récents: {len(data.get('paiements_recents', []))}")
            
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Contenu: {response.content}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")
    
    return True

if __name__ == '__main__':
    test_api_recherche()
