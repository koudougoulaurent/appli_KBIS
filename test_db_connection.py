#!/usr/bin/env python
"""
Test de connexion à la base de données PostgreSQL
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
os.environ['DATABASE_URL'] = 'postgresql://kbis_user:qN64K1DDSffwfTPThqEPgtsH5sVwwKGP@dpg-d3og40k9c44c73cvh1h0-a.oregon-postgres.render.com/kbis_immobilier'

try:
    django.setup()
    from django.db import connection
    
    print("✅ Configuration Django chargée")
    print("✅ Connexion à la base de données établie")
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Test de requête réussi: {result}")
        
    print("✅ Tous les tests passent!")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    sys.exit(1)
