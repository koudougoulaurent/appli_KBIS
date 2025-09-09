#!/usr/bin/env python
"""Script de debug pour identifier le problème d'import 'packages'"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test d'imports Django...")

try:
    # Test 1: Import Django de base
    print("1. Test import Django...")
    import django
    print(f"   ✅ Django {django.get_version()} importé")
except Exception as e:
    print(f"   ❌ Erreur Django: {e}")
    sys.exit(1)

try:
    # Test 2: Configuration Django
    print("2. Test configuration Django...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
    django.setup()
    print("   ✅ Configuration Django OK")
except Exception as e:
    print(f"   ❌ Erreur configuration: {e}")
    sys.exit(1)

try:
    # Test 3: Import des apps
    print("3. Test import des apps...")
    from core.models import *
    print("   ✅ Core importé")
except Exception as e:
    print(f"   ❌ Erreur core: {e}")

try:
    from proprietes.models import *
    print("   ✅ Proprietes importé")
except Exception as e:
    print(f"   ❌ Erreur proprietes: {e}")

try:
    from paiements.models import *
    print("   ✅ Paiements importé")
except Exception as e:
    print(f"   ❌ Erreur paiements: {e}")

try:
    from utilisateurs.models import *
    print("   ✅ Utilisateurs importé")
except Exception as e:
    print(f"   ❌ Erreur utilisateurs: {e}")

print("✅ Tests terminés")