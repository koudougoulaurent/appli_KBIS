#!/usr/bin/env python
"""
Script pour forcer la mise à jour du cache et corriger les problèmes d'URLs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
django.setup()

def clear_cache_and_restart():
    """Nettoie le cache et redémarre les services."""
    
    print("Nettoyage du cache et redemarrage...")
    print("=" * 50)
    
    try:
        # 1. Nettoyer le cache Django
        from django.core.cache import cache
        cache.clear()
        print("Cache Django nettoye")
        
        # 2. Collecter les fichiers statiques
        from django.core.management import call_command
        call_command('collectstatic', '--noinput', verbosity=0)
        print("Fichiers statiques collectes")
        
        # 3. Verifier les URLs
        from django.urls import reverse
        try:
            dashboard_url = reverse('core:dashboard_stats_api')
            print(f"URL API correcte: {dashboard_url}")
        except Exception as e:
            print(f"Erreur URL API: {e}")
        
        # 4. Verifier le fichier favicon
        import os
        favicon_path = os.path.join('static', 'favicon.ico')
        if os.path.exists(favicon_path):
            print(f"Favicon trouve: {favicon_path}")
        else:
            print(f"Favicon manquant: {favicon_path}")
        
        # 5. Verifier le fichier JavaScript
        js_path = os.path.join('static', 'js', 'dashboard-dynamic.js')
        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if '/api/dashboard-stats/' in content:
                    print("JavaScript corrige")
                else:
                    print("JavaScript non corrige")
        else:
            print(f"Fichier JavaScript manquant: {js_path}")
        
        print("\n" + "=" * 50)
        print("INSTRUCTIONS POUR L'UTILISATEUR")
        print("=" * 50)
        print("1. Videz le cache de votre navigateur:")
        print("   - Chrome/Edge: Ctrl+Shift+R ou F12 > Network > Disable cache")
        print("   - Firefox: Ctrl+Shift+R")
        print("2. Redemarrez votre navigateur")
        print("3. Accedez a: http://localhost:8000/dashboard/")
        print("4. Verifiez la console du navigateur (F12) pour les erreurs")
        
        print("\nURLs de test:")
        print("   - API: http://localhost:8000/api/dashboard-stats/")
        print("   - Favicon: http://localhost:8000/static/favicon.ico")
        print("   - Dashboard: http://localhost:8000/dashboard/")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {str(e)}")

if __name__ == "__main__":
    clear_cache_and_restart()
