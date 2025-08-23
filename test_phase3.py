#!/usr/bin/env python
"""
Script de test pour la Phase 3 - Contrats et Paiements
"""
import os
import django
import requests
import json
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from contrats.models import Contrat, Quittance, EtatLieux
from paiements.models import Paiement, Retrait, CompteBancaire

Utilisateur = get_user_model()

# Configuration pour les tests
BASE_URL = 'http://127.0.0.1:8000'
LOGIN_URL = f'{BASE_URL}/login/'
API_BASE = f'{BASE_URL}'

def test_database_data():
    """Teste les données en base."""
    print("🔍 Test des données en base...")
    
    # Vérifier les données existantes
    stats = {
        'utilisateurs': Utilisateur.objects.count(),
        'contrats': Contrat.objects.count(),
        'quittances': Quittance.objects.count(),
        'etats_lieux': EtatLieux.objects.count(),
        'paiements': Paiement.objects.count(),
        'retraits': Retrait.objects.count(),
        'comptes_bancaires': CompteBancaire.objects.count(),
    }
    
    print("📊 Données en base:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    # Vérifier qu'il y a des données
    if stats['contrats'] == 0:
        print("❌ Aucun contrat trouvé en base")
        return False
    
    if stats['paiements'] == 0:
        print("❌ Aucun paiement trouvé en base")
        return False
    
    print("✅ Données en base OK")
    return True


def test_api_endpoints():
    """Teste les endpoints API."""
    print("\n🌐 Test des endpoints API...")
    
    # Créer une session pour les tests
    session = requests.Session()
    
    # Se connecter
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code != 200:
            print("❌ Échec de la connexion")
            return False
        
        print("✅ Connexion réussie")
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Django est démarré")
        return False
    
    # Endpoints à tester
    endpoints = [
        # Contrats
        '/contrats/api/contrats/',
        '/contrats/api/contrats/stats/',
        '/contrats/api/contrats/actifs/',
        '/contrats/api/contrats/expirant_soon/',
        '/contrats/api/contrats/par_ville/',
        '/contrats/api/contrats/par_prix/',
        
        # Quittances
        '/contrats/api/quittances/',
        '/contrats/api/quittances/stats/',
        
        # États des lieux
        '/contrats/api/etats-lieux/',
        '/contrats/api/etats-lieux/stats/',
        
        # Paiements
        '/paiements/api/paiements/',
        '/paiements/api/paiements/stats/',
        '/paiements/api/paiements/en_attente/',
        '/paiements/api/paiements/valides/',
        '/paiements/api/paiements/par_type/',
        '/paiements/api/paiements/par_mois/',
        
        # Retraits
        '/paiements/api/retraits/',
        '/paiements/api/retraits/stats/',
        '/paiements/api/retraits/en_attente/',
        '/paiements/api/retraits/par_bailleur/',
        
        # Comptes bancaires
        '/paiements/api/comptes-bancaires/',
        '/paiements/api/comptes-bancaires/stats/',
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint in endpoints:
        try:
            url = f"{API_BASE}{endpoint}"
            response = session.get(url)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                success_count += 1
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Erreur: {e}")
    
    print(f"\n📊 Résultats API: {success_count}/{total_count} endpoints fonctionnels")
    return success_count == total_count


def test_dashboard():
    """Teste l'accès au dashboard."""
    print("\n📊 Test du dashboard...")
    
    session = requests.Session()
    
    try:
        # Se connecter
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code != 200:
            print("❌ Échec de la connexion pour le dashboard")
            return False
        
        # Accéder au dashboard
        dashboard_url = f"{BASE_URL}/"
        response = session.get(dashboard_url)
        
        if response.status_code == 200:
            print("✅ Dashboard accessible")
            return True
        else:
            print(f"❌ Dashboard - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur dashboard: {e}")
        return False


def test_admin_interface():
    """Teste l'interface d'administration."""
    print("\n⚙️ Test de l'interface d'administration...")
    
    session = requests.Session()
    
    try:
        # Se connecter
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code != 200:
            print("❌ Échec de la connexion pour l'admin")
            return False
        
        # Accéder à l'admin
        admin_url = f"{BASE_URL}/admin/"
        response = session.get(admin_url)
        
        if response.status_code == 200:
            print("✅ Interface d'administration accessible")
            return True
        else:
            print(f"❌ Admin - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur admin: {e}")
        return False


def main():
    """Fonction principale."""
    print("🧪 TEST PHASE 3 - CONTRATS ET PAIEMENTS")
    print("=" * 50)
    
    results = []
    
    # 1. Test des données en base
    results.append(('Données en base', test_database_data()))
    
    # 2. Test des endpoints API
    results.append(('Endpoints API', test_api_endpoints()))
    
    # 3. Test du dashboard
    results.append(('Dashboard', test_dashboard()))
    
    # 4. Test de l'interface d'administration
    results.append(('Interface Admin', test_admin_interface()))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    success_count = 0
    total_count = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            success_count += 1
    
    print(f"\n📊 Résultats: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La Phase 3 est entièrement fonctionnelle")
    else:
        print(f"\n⚠️ {total_count - success_count} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus")
    
    print("\n🌐 Accès:")
    print("   - Dashboard: http://127.0.0.1:8000/")
    print("   - Admin: http://127.0.0.1:8000/admin/")
    print("   - API Contrats: http://127.0.0.1:8000/contrats/api/")
    print("   - API Paiements: http://127.0.0.1:8000/paiements/api/")


if __name__ == '__main__':
    main() 