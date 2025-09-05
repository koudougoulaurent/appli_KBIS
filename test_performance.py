#!/usr/bin/env python
"""
Script de test de performance pour l'application Django
"""
import os
import sys
import django
import time
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

Utilisateur = get_user_model()

class PerformanceTester:
    """Classe pour tester les performances de l'application"""
    
    def __init__(self):
        self.client = Client()
        self.results = []
        self.base_url = "http://127.0.0.1:8000"
        
    def test_page_load(self, url, description, auth_required=True):
        """Teste le temps de chargement d'une page"""
        print(f"\n🔍 Test: {description}")
        print(f"   URL: {url}")
        
        if auth_required:
            # Se connecter en tant qu'utilisateur test
            user = Utilisateur.objects.filter(is_superuser=True).first()
            if user:
                self.client.force_login(user)
            else:
                print("   ❌ Aucun utilisateur superuser trouvé")
                return
        
        # Premier accès (sans cache)
        start_time = time.time()
        response = self.client.get(url)
        first_load_time = time.time() - start_time
        
        # Deuxième accès (avec cache potentiel)
        start_time = time.time()
        response2 = self.client.get(url)
        second_load_time = time.time() - start_time
        
        # Troisième accès (cache confirmé)
        start_time = time.time()
        response3 = self.client.get(url)
        third_load_time = time.time() - start_time
        
        result = {
            'url': url,
            'description': description,
            'first_load': first_load_time,
            'second_load': second_load_time,
            'third_load': third_load_time,
            'improvement': ((first_load_time - third_load_time) / first_load_time) * 100,
            'status_code': response.status_code
        }
        
        self.results.append(result)
        
        print(f"   📊 Premier chargement: {first_load_time:.3f}s")
        print(f"   📊 Deuxième chargement: {second_load_time:.3f}s")
        print(f"   📊 Troisième chargement: {third_load_time:.3f}s")
        print(f"   🚀 Amélioration: {result['improvement']:.1f}%")
        print(f"   ✅ Statut: {response.status_code}")
        
        if result['improvement'] > 20:
            print(f"   🎉 Excellente amélioration!")
        elif result['improvement'] > 10:
            print(f"   👍 Bonne amélioration")
        else:
            print(f"   ⚠️ Amélioration limitée")
    
    def test_cache_efficiency(self):
        """Teste l'efficacité du cache"""
        print("\n🧪 Test de l'efficacité du cache")
        
        # Vérifier les clés de cache
        cache_keys = [
            'dashboard_stats_1',
            'user_permissions_1',
            'user_modules_1',
            'devise_F CFA'
        ]
        
        for key in cache_keys:
            value = cache.get(key)
            if value:
                print(f"   ✅ Cache actif: {key}")
            else:
                print(f"   ❌ Cache vide: {key}")
    
    def test_database_queries(self):
        """Teste les requêtes de base de données"""
        print("\n🗄️ Test des requêtes de base de données")
        
        from django.db import connection
        from django.test.utils import override_settings
        
        # Réinitialiser le compteur de requêtes
        connection.queries = []
        
        # Test avec une vue simple
        with override_settings(DEBUG=True):
            start_time = time.time()
            response = self.client.get('/')
            load_time = time.time() - start_time
            
            query_count = len(connection.queries)
            
            print(f"   📊 Temps de chargement: {load_time:.3f}s")
            print(f"   📊 Nombre de requêtes: {query_count}")
            
            if query_count < 10:
                print(f"   ✅ Excellent: Moins de 10 requêtes")
            elif query_count < 20:
                print(f"   👍 Bon: Moins de 20 requêtes")
            else:
                print(f"   ⚠️ À améliorer: {query_count} requêtes")
    
    def generate_report(self):
        """Génère un rapport de performance"""
        print("\n" + "="*60)
        print("📊 RAPPORT DE PERFORMANCE")
        print("="*60)
        
        if not self.results:
            print("Aucun test effectué")
            return
        
        total_improvement = sum(r['improvement'] for r in self.results)
        avg_improvement = total_improvement / len(self.results)
        
        print(f"📈 Amélioration moyenne: {avg_improvement:.1f}%")
        print(f"🔢 Nombre de pages testées: {len(self.results)}")
        
        print("\n📋 Détail par page:")
        for result in self.results:
            status_icon = "✅" if result['status_code'] == 200 else "❌"
            print(f"   {status_icon} {result['description']}")
            print(f"      Amélioration: {result['improvement']:.1f}%")
            print(f"      Temps final: {result['third_load']:.3f}s")
        
        # Recommandations
        print("\n💡 Recommandations:")
        if avg_improvement > 30:
            print("   🎉 Excellentes performances! Le cache fonctionne parfaitement.")
        elif avg_improvement > 20:
            print("   👍 Bonnes performances. Le cache apporte une amélioration notable.")
        elif avg_improvement > 10:
            print("   ⚠️ Performances correctes. Considérez d'ajuster les timeouts de cache.")
        else:
            print("   ❌ Performances limitées. Vérifiez la configuration du cache.")
    
    def run_all_tests(self):
        """Exécute tous les tests de performance"""
        print("🚀 Démarrage des tests de performance")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Tests des pages principales
        self.test_page_load('/', 'Page d\'accueil', auth_required=True)
        self.test_page_load('/dashboard/', 'Dashboard principal', auth_required=True)
        self.test_page_load('/proprietes/', 'Liste des propriétés', auth_required=True)
        self.test_page_load('/contrats/', 'Liste des contrats', auth_required=True)
        self.test_page_load('/paiements/', 'Liste des paiements', auth_required=True)
        
        # Tests spécifiques
        self.test_cache_efficiency()
        self.test_database_queries()
        
        # Rapport final
        self.generate_report()

def main():
    """Fonction principale"""
    print("🔧 Testeur de Performance - GESTIMMOB")
    print("="*50)
    
    try:
        tester = PerformanceTester()
        tester.run_all_tests()
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
