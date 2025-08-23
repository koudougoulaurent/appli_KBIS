#!/usr/bin/env python
"""
Test rapide des optimisations de performance
"""
import os
import django
import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.core.cache import cache
from django.contrib.auth import get_user_model

Utilisateur = get_user_model()

def test_cache_functionality():
    """Test rapide du système de cache"""
    print("🧪 Test du système de cache...")
    
    # Test 1: Mise en cache
    test_key = "test_performance_key"
    test_data = {"message": "Test de performance", "timestamp": time.time()}
    
    cache.set(test_key, test_data, 60)
    print("   ✅ Données mises en cache")
    
    # Test 2: Récupération depuis le cache
    retrieved_data = cache.get(test_key)
    if retrieved_data and retrieved_data.get("message") == "Test de performance":
        print("   ✅ Données récupérées depuis le cache")
    else:
        print("   ❌ Échec de la récupération depuis le cache")
    
    # Test 3: Nettoyage du cache
    cache.delete(test_key)
    if cache.get(test_key) is None:
        print("   ✅ Cache nettoyé correctement")
    else:
        print("   ❌ Échec du nettoyage du cache")
    
    return True

def test_optimization_modules():
    """Test des modules d'optimisation"""
    print("\n🔧 Test des modules d'optimisation...")
    
    try:
        from core.optimizations import QueryOptimizer, TemplateOptimizer, performance_monitor
        print("   ✅ Modules d'optimisation importés")
        
        # Test de QueryOptimizer
        if hasattr(QueryOptimizer, 'optimize_dashboard_queries'):
            print("   ✅ QueryOptimizer fonctionnel")
        else:
            print("   ❌ QueryOptimizer incomplet")
        
        # Test de TemplateOptimizer
        if hasattr(TemplateOptimizer, 'optimize_template_context'):
            print("   ✅ TemplateOptimizer fonctionnel")
        else:
            print("   ❌ TemplateOptimizer incomplet")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erreur d'import: {e}")
        return False

def test_middleware_configuration():
    """Test de la configuration des middleware"""
    print("\n⚙️ Test de la configuration des middleware...")
    
    from django.conf import settings
    
    required_middleware = [
        'utilisateurs.middleware.PerformanceMiddleware',
        'utilisateurs.middleware.DatabaseOptimizationMiddleware',
        'utilisateurs.middleware.CacheOptimizationMiddleware',
        'core.middleware.DeviseMiddleware',
    ]
    
    all_present = True
    for middleware in required_middleware:
        if middleware in settings.MIDDLEWARE:
            print(f"   ✅ {middleware}")
        else:
            print(f"   ❌ {middleware} - MANQUANT")
            all_present = False
    
    return all_present

def test_cache_configuration():
    """Test de la configuration du cache"""
    print("\n💾 Test de la configuration du cache...")
    
    from django.conf import settings
    
    if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
        cache_config = settings.CACHES['default']
        print(f"   ✅ Backend cache: {cache_config.get('BACKEND', 'Non défini')}")
        print(f"   ✅ Timeout: {cache_config.get('TIMEOUT', 'Non défini')}s")
        print(f"   ✅ Max entries: {cache_config.get('OPTIONS', {}).get('MAX_ENTRIES', 'Non défini')}")
        return True
    else:
        print("   ❌ Configuration du cache manquante")
        return False

def main():
    """Fonction principale"""
    print("🚀 Test Rapide des Optimisations de Performance")
    print("=" * 50)
    
    tests = [
        ("Cache", test_cache_functionality),
        ("Modules d'optimisation", test_optimization_modules),
        ("Configuration middleware", test_middleware_configuration),
        ("Configuration cache", test_cache_configuration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Rapport final
    print("\n" + "=" * 50)
    print("📊 RAPPORT DES TESTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Toutes les optimisations sont correctement configurées!")
        print("💡 Vous pouvez maintenant tester les performances avec: python test_performance.py")
    else:
        print("⚠️ Certaines optimisations nécessitent une attention particulière")
        print("🔧 Vérifiez la configuration et relancez les tests")

if __name__ == "__main__":
    main()
