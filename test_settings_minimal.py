#!/usr/bin/env python
"""
Test avec settings minimaux pour identifier le problème packages
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
    
    # Test des INSTALLED_APPS
    print(f"📋 INSTALLED_APPS: {settings.INSTALLED_APPS}")
    
    # Test des MIDDLEWARE
    print(f"📋 MIDDLEWARE: {settings.MIDDLEWARE}")
    
    # Test des TEMPLATES
    print(f"📋 TEMPLATES: {settings.TEMPLATES}")
    
    # Test de setup Django
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
        for app in settings.INSTALLED_APPS:
            if not app.startswith('django.'):
                try:
                    __import__(app)
                    print(f"✅ {app} OK")
                except Exception as e2:
                    print(f"❌ {app}: {e2}")
                    if 'packages' in str(e2):
                        print(f"   🔍 Erreur 'packages' dans {app}!")
                        
    except Exception as e3:
        print(f"❌ Erreur settings: {e3}")
        if 'packages' in str(e3):
            print("   🔍 Erreur 'packages' dans settings!")
