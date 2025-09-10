#!/usr/bin/env python
"""
Script de debug final pour identifier le problème 'packages'
"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Diagnostic final du problème 'packages'...")

try:
    print("\n1. Test import Django...")
    import django
    print(f"   ✅ Django {django.get_version()}")
except Exception as e:
    print(f"   ❌ Erreur Django: {e}")
    sys.exit(1)

try:
    print("\n2. Test configuration Django...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
    
    # Essayer d'importer les settings directement
    print("   - Import des settings...")
    from gestion_immobiliere import settings
    print("   ✅ Settings importés")
    
    # Essayer de configurer Django
    print("   - Configuration Django...")
    django.setup()
    print("   ✅ Configuration Django OK")
    
except Exception as e:
    print(f"   ❌ Erreur configuration: {e}")
    print(f"   Type d'erreur: {type(e).__name__}")
    if 'packages' in str(e):
        print("   🔍 Erreur 'packages' détectée!")
        
        # Essayer d'importer les apps une par une
        print("\n3. Test import des apps individuelles...")
        apps = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications', 'bailleurs']
        
        for app in apps:
            try:
                print(f"   - Test import {app}...")
                __import__(app)
                print(f"   ✅ {app} importé")
            except Exception as e2:
                print(f"   ❌ Erreur {app}: {e2}")
                if 'packages' in str(e2):
                    print(f"   🔍 Erreur 'packages' dans {app}!")
                    
                    # Essayer d'importer les modules de l'app un par un
                    try:
                        print(f"     - Test import {app}.models...")
                        __import__(f"{app}.models")
                        print(f"     ✅ {app}.models importé")
                    except Exception as e3:
                        print(f"     ❌ Erreur {app}.models: {e3}")
                        if 'packages' in str(e3):
                            print(f"     🔍 Erreur 'packages' dans {app}.models!")
                    
                    try:
                        print(f"     - Test import {app}.views...")
                        __import__(f"{app}.views")
                        print(f"     ✅ {app}.views importé")
                    except Exception as e4:
                        print(f"     ❌ Erreur {app}.views: {e4}")
                        if 'packages' in str(e4):
                            print(f"     🔍 Erreur 'packages' dans {app}.views!")
                    
                    try:
                        print(f"     - Test import {app}.urls...")
                        __import__(f"{app}.urls")
                        print(f"     ✅ {app}.urls importé")
                    except Exception as e5:
                        print(f"     ❌ Erreur {app}.urls: {e5}")
                        if 'packages' in str(e5):
                            print(f"     🔍 Erreur 'packages' dans {app}.urls!")
    
    sys.exit(1)

print("\n✅ Diagnostic terminé - Django fonctionne correctement!")
