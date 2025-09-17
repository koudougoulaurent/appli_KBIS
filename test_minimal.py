#!/usr/bin/env python
"""
Test minimal pour identifier le problème packages
"""

import os
import sys

# Configuration Django minimale
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    import django
    print("✅ Django importé")
    
    # Test des settings
    from django.conf import settings
    print("✅ Settings chargés")
    
    # Test des apps une par une
    apps = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications']
    
    for app in apps:
        try:
            __import__(f'{app}.models')
            print(f"✅ {app}.models OK")
        except Exception as e:
            print(f"❌ {app}.models: {e}")
            if 'packages' in str(e):
                print(f"   🔍 Erreur 'packages' dans {app}.models!")
        
        try:
            __import__(f'{app}.views')
            print(f"✅ {app}.views OK")
        except Exception as e:
            print(f"❌ {app}.views: {e}")
            if 'packages' in str(e):
                print(f"   🔍 Erreur 'packages' dans {app}.views!")
        
        try:
            __import__(f'{app}.urls')
            print(f"✅ {app}.urls OK")
        except Exception as e:
            print(f"❌ {app}.urls: {e}")
            if 'packages' in str(e):
                print(f"   🔍 Erreur 'packages' dans {app}.urls!")

except Exception as e:
    print(f"❌ Erreur critique: {e}")
    if 'packages' in str(e):
        print("   🔍 Erreur 'packages' détectée!")
