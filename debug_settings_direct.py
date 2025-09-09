#!/usr/bin/env python
"""Script de debug pour tester les settings directement"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test des settings directement...")

try:
    print("1. Test import gestion_immobiliere.settings...")
    import gestion_immobiliere.settings as settings
    print("   ✅ Settings importé directement")
    
    print("2. Test INSTALLED_APPS...")
    for app in settings.INSTALLED_APPS:
        print(f"   - {app}")
    
    print("3. Test import des apps depuis settings...")
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django.'):
            try:
                __import__(app)
                print(f"   ✅ {app} importé")
            except Exception as e:
                print(f"   ❌ {app}: {e}")
                
except Exception as e:
    print(f"   ❌ Erreur settings: {e}")
    print(f"   Détail: {type(e).__name__}: {e}")

print("✅ Tests terminés")
