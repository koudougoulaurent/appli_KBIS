#!/usr/bin/env python
"""Script de debug pour tester les context processors"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test des context processors...")

try:
    print("1. Test import core.models...")
    from core.models import Devise
    print("   ✅ Devise importé")
except Exception as e:
    print(f"   ❌ Erreur Devise: {e}")

try:
    print("2. Test import context_processors...")
    from core.context_processors import devise_active, devises_actives
    print("   ✅ Context processors importés")
except Exception as e:
    print(f"   ❌ Erreur context processors: {e}")

print("✅ Tests terminés")
