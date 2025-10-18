#!/usr/bin/env python
"""
Test direct de lecture du fichier settings
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
    
    # Lire directement le fichier
    with open('gestion_immobiliere/settings_postgresql.py', 'r') as f:
        content = f.read()
        print("Fichier settings lu")
        print(f"Contenu contient DATABASES: {'DATABASES' in content}")
        print(f"Contenu contient ENGINE: {'ENGINE' in content}")
        
    print("Test termine")
        
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
