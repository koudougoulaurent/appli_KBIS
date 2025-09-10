#!/usr/bin/env python
"""
Test Django minimal sans les apps locales
"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test Django minimal...")

try:
    print("\n1. Test import Django...")
    import django
    print(f"   ✅ Django {django.get_version()}")
except Exception as e:
    print(f"   ❌ Erreur Django: {e}")
    sys.exit(1)

try:
    print("\n2. Test configuration Django minimal...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
    
    # Essayer d'importer les settings directement
    print("   - Import des settings...")
    from gestion_immobiliere import settings_minimal
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
    sys.exit(1)

print("\n✅ Test terminé - Django fonctionne correctement!")
