#!/usr/bin/env python3
"""
Script de test pour l'API d'audit en temps réel
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/audit/realtime/"
NOTIFICATIONS_URL = f"{BASE_URL}/api/audit/notifications/"

def test_audit_api():
    """Test de l'API d'audit en temps réel"""
    print("🧪 Test de l'API d'audit en temps réel")
    print("=" * 50)
    
    try:
        # Test de l'API principale
        print(f"📡 Test de l'API: {API_URL}")
        response = requests.get(API_URL)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API accessible")
            print(f"📊 Données reçues: {len(data.get('data', {}).get('logs', []))} logs")
            print(f"🕒 Timestamp: {data.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"📝 Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur Django")
        print("💡 Assurez-vous que le serveur est démarré: python manage.py runserver")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

def test_notifications_api():
    """Test de l'API des notifications"""
    print("\n🔔 Test de l'API des notifications")
    print("=" * 50)
    
    try:
        # Test avec timestamp actuel
        now = datetime.now().isoformat()
        params = {'last_check': now}
        
        print(f"📡 Test des notifications: {NOTIFICATIONS_URL}")
        response = requests.get(NOTIFICATIONS_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API des notifications accessible")
            print(f"📊 Notifications: {data.get('count', 0)}")
        else:
            print(f"❌ Erreur API notifications: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_page_access():
    """Test d'accès à la page d'audit"""
    print("\n🌐 Test d'accès à la page d'audit")
    print("=" * 50)
    
    try:
        page_url = f"{BASE_URL}/rapports-audit/"
        print(f"📡 Test de la page: {page_url}")
        
        response = requests.get(page_url)
        
        if response.status_code == 200:
            print("✅ Page accessible")
            if "Audit Realtime Manager" in response.text:
                print("✅ JavaScript en temps réel détecté")
            else:
                print("⚠️  JavaScript en temps réel non détecté")
        else:
            print(f"❌ Erreur page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de l'API d'audit")
    print(f"📍 Serveur: {BASE_URL}")
    print()
    
    test_audit_api()
    test_notifications_api()
    test_page_access()
    
    print("\n✨ Tests terminés")
