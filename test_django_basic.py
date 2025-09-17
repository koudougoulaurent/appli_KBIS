#!/usr/bin/env python
"""
Test Django de base pour identifier le problème packages
"""

import os
import sys

# Configuration Django minimale
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    import django
    print("✅ Django importé")
    
    # Test de setup Django
    django.setup()
    print("✅ Django setup OK")
    
except Exception as e:
    print(f"❌ Erreur Django setup: {e}")
    if 'packages' in str(e):
        print("   🔍 Erreur 'packages' détectée!")
    
    # Test des imports individuels
    try:
        from django.conf import settings
        print("✅ Settings importé")
    except Exception as e2:
        print(f"❌ Erreur settings: {e2}")
        if 'packages' in str(e2):
            print("   🔍 Erreur 'packages' dans settings!")
    
    # Test des apps une par une
    apps = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications']
    
    for app in apps:
        try:
            __import__(f'{app}')
            print(f"✅ {app} OK")
        except Exception as e3:
            print(f"❌ {app}: {e3}")
            if 'packages' in str(e3):
                print(f"   🔍 Erreur 'packages' dans {app}!")
