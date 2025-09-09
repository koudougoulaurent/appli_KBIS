#!/usr/bin/env python
"""Script de debug pour tester l'initialisation de Django étape par étape"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test de l'initialisation de Django étape par étape...")

try:
    print("1. Test import django...")
    import django
    print(f"   ✅ Django {django.get_version()} importé")
except Exception as e:
    print(f"   ❌ Erreur Django: {e}")
    sys.exit(1)

try:
    print("2. Test configuration Django...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
    print("   ✅ DJANGO_SETTINGS_MODULE défini")
except Exception as e:
    print(f"   ❌ Erreur configuration: {e}")
    sys.exit(1)

try:
    print("3. Test django.setup()...")
    django.setup()
    print("   ✅ django.setup() réussi")
except Exception as e:
    print(f"   ❌ Erreur django.setup(): {e}")
    print(f"   Détail: {type(e).__name__}: {e}")
    sys.exit(1)

try:
    print("4. Test import des apps après setup...")
    from core.models import Devise
    print("   ✅ Devise importé après setup")
except Exception as e:
    print(f"   ❌ Erreur Devise après setup: {e}")

print("✅ Tests terminés")
