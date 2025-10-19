#!/usr/bin/env python
"""
Script pour démarrer le serveur Django avec optimisations
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def start_optimized_server():
    """Démarre le serveur avec les optimisations activées"""
    print("Démarrage du serveur Django optimisé...")
    print("=" * 50)
    
    # Configuration Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
    django.setup()
    
    # Vérifier les optimisations
    from django.conf import settings
    
    print("Vérification des optimisations:")
    print("-" * 30)
    
    # Vérifier le cache
    if hasattr(settings, 'CACHES'):
        print("✓ Cache configuré")
    else:
        print("✗ Cache non configuré")
    
    # Vérifier les middlewares d'optimisation
    optimization_middlewares = [
        'core.performance_middleware.PerformanceMiddleware',
        'core.performance_middleware.CacheOptimizationMiddleware',
        'core.performance_middleware.DatabaseOptimizationMiddleware',
        'core.performance_middleware.StaticFilesOptimizationMiddleware',
        'core.performance_middleware.AntiRefreshLoopMiddleware',
    ]
    
    active_middlewares = 0
    for middleware in optimization_middlewares:
        if middleware in settings.MIDDLEWARE:
            active_middlewares += 1
    
    print(f"✓ {active_middlewares}/{len(optimization_middlewares)} middlewares d'optimisation actifs")
    
    # Vérifier les fichiers d'optimisation
    js_files = [
        'static/js/dashboard-optimizer.js',
        'static/js/dashboard-dynamic.js'
    ]
    
    existing_files = 0
    for js_file in js_files:
        if os.path.exists(js_file):
            existing_files += 1
    
    print(f"✓ {existing_files}/{len(js_files)} fichiers JavaScript d'optimisation présents")
    
    # Vérifier l'optimiseur de dashboard
    try:
        from core.optimizations_dashboard import DashboardOptimizer
        print("✓ Optimiseur de dashboard disponible")
    except ImportError:
        print("✗ Optimiseur de dashboard manquant")
    
    print("\n" + "=" * 50)
    print("Serveur optimisé prêt!")
    print("=" * 50)
    print("Accédez à: http://127.0.0.1:8000/core/dashboard/")
    print("Le dashboard est maintenant fluide et optimisé!")
    print("\nAppuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 50)
    
    # Démarrer le serveur
    try:
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
    except KeyboardInterrupt:
        print("\n\nServeur arrêté par l'utilisateur")
    except Exception as e:
        print(f"\nErreur lors du démarrage: {e}")

if __name__ == '__main__':
    start_optimized_server()
