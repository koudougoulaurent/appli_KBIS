#!/usr/bin/env python3
"""
Script de test pour vérifier les endpoints API de gestion des cautions
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINTS = {
    "contrats_cautions": f"{BASE_URL}/contrats/api/cautions/",
    "paiements_cautions": f"{BASE_URL}/paiements/api/cautions-avances/",
    "core_cautions": f"{BASE_URL}/core/api/cautions/",
}

def test_endpoint(url, description):
    """Teste un endpoint API et affiche le résultat"""
    print(f"\n🔍 Test de {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    if 'count' in data:
                        print(f"✅ Succès: {data.get('count', 'N/A')} éléments trouvés")
                    elif 'statistiques' in data:
                        print(f"✅ Succès: Statistiques récupérées")
                    else:
                        print(f"✅ Succès: Données récupérées ({len(data)} clés)")
                else:
                    print(f"✅ Succès: {len(data)} éléments dans la liste")
            except json.JSONDecodeError:
                print(f"⚠️  Réponse reçue mais pas de JSON valide")
                print(f"Contenu: {response.text[:200]}...")
        elif response.status_code == 401:
            print("🔒 Authentification requise (normal)")
        elif response.status_code == 403:
            print("🚫 Accès interdit")
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"Contenu: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion - Le serveur n'est peut-être pas démarré")
    except requests.exceptions.Timeout:
        print("⏰ Timeout - Le serveur met trop de temps à répondre")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

def test_api_root():
    """Teste l'API root pour voir les endpoints disponibles"""
    print("\n🏠 Test de l'API Root")
    print(f"URL: {BASE_URL}/contrats/")
    
    try:
        response = requests.get(f"{BASE_URL}/contrats/", timeout=10)
        if response.status_code == 200:
            print("✅ API root accessible")
            # Vérifier si l'endpoint des cautions est visible
            if "api/cautions" in response.text:
                print("✅ Endpoint des cautions visible dans l'API root")
            else:
                print("⚠️  Endpoint des cautions non visible dans l'API root")
        else:
            print(f"❌ API root non accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API root: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 Test des Endpoints API de Gestion des Cautions")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Test de l'API root
    test_api_root()
    
    # Test des endpoints spécifiques
    for name, url in API_ENDPOINTS.items():
        test_endpoint(url, name)
    
    print("\n" + "=" * 60)
    print("🏁 Tests terminés")
    print("\n📋 Résumé des endpoints testés:")
    for name, url in API_ENDPOINTS.items():
        print(f"  • {name}: {url}")
    
    print("\n💡 Notes:")
    print("  - Les erreurs 401 (authentification) sont normales")
    print("  - Vérifiez que le serveur Django est démarré")
    print("  - Connectez-vous pour tester les fonctionnalités complètes")

if __name__ == "__main__":
    main()
