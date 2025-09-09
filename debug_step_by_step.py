#!/usr/bin/env python
"""Script de debug étape par étape pour identifier le problème 'packages'"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test d'imports étape par étape...")

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
    print(f"   Détail de l'erreur: {type(e).__name__}: {e}")
    sys.exit(1)

print("✅ Tests terminés avec succès")
