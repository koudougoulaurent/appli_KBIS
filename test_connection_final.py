#!/usr/bin/env python
"""
Test final de connexion à la base de données
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
        
        # Test de connexion avec la configuration du module
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