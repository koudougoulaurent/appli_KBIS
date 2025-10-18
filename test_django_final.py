#!/usr/bin/env python
"""
Test final de configuration Django
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
        
        # Test de connexion
        django.setup()
        from django.db import connection
        
        print("Connexion a la base de donnees etablie")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"Test de requete reussi: {result}")
            
        print("Tous les tests passent!")
    else:
        print("Pas de configuration de base de donnees trouvee")
        
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
