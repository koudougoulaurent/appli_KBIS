#!/usr/bin/env python
"""
Test d'import direct du module settings
"""
import os
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')

try:
    import django
    from django.conf import settings
    
    print("Configuration Django chargee")
    print(f"INSTALLED_APPS: {len(settings.INSTALLED_APPS)}")
    print(f"DATABASES keys: {list(settings.DATABASES.keys())}")
    
    # Import direct du module
    import gestion_immobiliere.settings_postgresql as settings_module
    print(f"Module settings importe: {settings_module}")
    print(f"DATABASES dans le module: {hasattr(settings_module, 'DATABASES')}")
    
    if hasattr(settings_module, 'DATABASES'):
        print(f"DATABASES: {settings_module.DATABASES}")
        print(f"ENGINE: {settings_module.DATABASES['default']['ENGINE']}")
        print(f"NAME: {settings_module.DATABASES['default']['NAME']}")
        print(f"HOST: {settings_module.DATABASES['default']['HOST']}")
        
    print("Test termine")
        
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
