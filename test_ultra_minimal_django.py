#!/usr/bin/env python
"""
Test Django ultra-minimal pour identifier le problème packages
"""

import os
import sys

# Configuration Django ultra-minimale
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    import django
    print("✅ Django importé")
    
    # Test des settings
    from django.conf import settings
    print("✅ Settings chargés")
    
    # Test des apps une par une AVANT django.setup()
    apps = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications']
    
    for app in apps:
        try:
            __import__(f'{app}')
            print(f"✅ {app} OK")
        except Exception as e:
            print(f"❌ {app}: {e}")
            if 'packages' in str(e):
                print(f"   🔍 Erreur 'packages' dans {app}!")
    
    # Test de django.setup()
    print("\n🔧 Test de django.setup()...")
    django.setup()
    print("✅ Django setup OK")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    if 'packages' in str(e):
        print("   🔍 Erreur 'packages' détectée!")
    
    # Test des imports individuels
    try:
        from django.conf import settings
        print("✅ Settings importé")
        
        # Test des apps une par une
        for app in apps:
            try:
                __import__(f'{app}')
                print(f"✅ {app} OK")
            except Exception as e2:
                print(f"❌ {app}: {e2}")
                if 'packages' in str(e2):
                    print(f"   🔍 Erreur 'packages' dans {app}!")
                    
    except Exception as e3:
        print(f"❌ Erreur settings: {e3}")
        if 'packages' in str(e3):
            print("   🔍 Erreur 'packages' dans settings!")
