#!/usr/bin/env python
"""Script de debug pour tester les settings individuellement"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test des settings individuellement...")

try:
    print("1. Test import settings...")
    from gestion_immobiliere import settings
    print("   ✅ Settings importé")
except Exception as e:
    print(f"   ❌ Erreur settings: {e}")
    print(f"   Détail de l'erreur: {type(e).__name__}: {e}")
    sys.exit(1)

try:
    print("2. Test INSTALLED_APPS...")
    for app in settings.INSTALLED_APPS:
        print(f"   - {app}")
    print("   ✅ INSTALLED_APPS OK")
except Exception as e:
    print(f"   ❌ Erreur INSTALLED_APPS: {e}")

try:
    print("3. Test MIDDLEWARE...")
    for middleware in settings.MIDDLEWARE:
        print(f"   - {middleware}")
    print("   ✅ MIDDLEWARE OK")
except Exception as e:
    print(f"   ❌ Erreur MIDDLEWARE: {e}")

print("✅ Tests terminés")
