#!/usr/bin/env python
"""
Test simple de configuration Django
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
    
    if 'default' in settings.DATABASES:
        print(f"ENGINE: {settings.DATABASES['default']['ENGINE']}")
        print(f"NAME: {settings.DATABASES['default']['NAME']}")
        print(f"HOST: {settings.DATABASES['default']['HOST']}")
    else:
        print("Pas de configuration de base de donnees trouvee")
        
    print("Test termine")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)