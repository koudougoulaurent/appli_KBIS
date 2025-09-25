#!/usr/bin/env python
"""
Script pour tester PostgreSQL en local (optionnel)
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_local_config():
    """Teste la configuration locale"""
    print("🔍 Test de la configuration locale...")
    
    from django.conf import settings
    
    # Vérifier la configuration de base de données
    db_config = settings.DATABASES['default']
    print(f"📊 Base de données: {db_config['ENGINE']}")
    print(f"📁 Fichier: {db_config.get('NAME', 'N/A')}")
    
    # Tester la connexion
    try:
        from django.db import connections
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Connexion locale réussie!")
    except Exception as e:
        print(f"❌ Erreur de connexion locale: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Test de configuration locale...")
    print("=" * 50)
    
    if test_local_config():
        print("\n✅ Configuration locale OK!")
        print("💡 En local, l'application utilise SQLite")
        print("🌐 Sur Render, l'application utilisera PostgreSQL")
    else:
        print("\n❌ Problème de configuration locale")
