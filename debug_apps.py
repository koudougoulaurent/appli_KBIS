#!/usr/bin/env python
"""Script de debug pour tester les imports des apps individuellement"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test d'imports des apps individuellement...")

# Test des imports sans Django
try:
    print("1. Test import core...")
    import core
    print("   ✅ Core importé")
except Exception as e:
    print(f"   ❌ Erreur core: {e}")

try:
    print("2. Test import proprietes...")
    import proprietes
    print("   ✅ Proprietes importé")
except Exception as e:
    print(f"   ❌ Erreur proprietes: {e}")

try:
    print("3. Test import paiements...")
    import paiements
    print("   ✅ Paiements importé")
except Exception as e:
    print(f"   ❌ Erreur paiements: {e}")

try:
    print("4. Test import utilisateurs...")
    import utilisateurs
    print("   ✅ Utilisateurs importé")
except Exception as e:
    print(f"   ❌ Erreur utilisateurs: {e}")

try:
    print("5. Test import contrats...")
    import contrats
    print("   ✅ Contrats importé")
except Exception as e:
    print(f"   ❌ Erreur contrats: {e}")

try:
    print("6. Test import notifications...")
    import notifications
    print("   ✅ Notifications importé")
except Exception as e:
    print(f"   ❌ Erreur notifications: {e}")

print("✅ Tests terminés")
