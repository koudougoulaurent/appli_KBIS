#!/usr/bin/env python
"""
Script de migration des données de SQLite vers PostgreSQL
Usage: python CONFIG/migrate_to_postgresql.py
"""
import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire parent au path Python
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from django.conf import settings
import json

def check_database_connection():
    """Vérifie la connexion à la base de données PostgreSQL"""
    try:
        db_conn = connections['default']
        db_conn.cursor()
        print("✅ Connexion à PostgreSQL réussie!")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion à PostgreSQL: {e}")
        return False

def export_data_from_sqlite():
    """Exporte les données de SQLite vers des fichiers JSON"""
    print("📤 Export des données depuis SQLite...")
    
    # Changer temporairement vers SQLite pour l'export
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
    
    # Exporter les données
    try:
        call_command('dumpdata', '--natural-foreign', '--natural-primary', 
                    '--exclude=contenttypes', '--exclude=auth.Permission',
                    output='CONFIG/data_export.json')
        print("✅ Export des données terminé!")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        return False

def import_data_to_postgresql():
    """Importe les données dans PostgreSQL"""
    print("📥 Import des données vers PostgreSQL...")
    
    try:
        # Changer vers PostgreSQL
        import dj_database_url
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        if DATABASE_URL:
            settings.DATABASES['default'] = dj_database_url.parse(DATABASE_URL)
        else:
            print("❌ DATABASE_URL non définie!")
            return False
        
        # Créer les tables
        call_command('migrate', '--run-syncdb')
        
        # Importer les données
        call_command('loaddata', 'CONFIG/data_export.json')
        
        print("✅ Import des données terminé!")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'import: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Migration SQLite vers PostgreSQL")
    print("=" * 50)
    
    # Vérifier que DATABASE_URL est définie
    if not os.environ.get('DATABASE_URL'):
        print("❌ Variable d'environnement DATABASE_URL non définie!")
        print("Définissez-la avec les informations de votre base PostgreSQL Render:")
        print("export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    # Vérifier la connexion PostgreSQL
    if not check_database_connection():
        return False
    
    # Exporter depuis SQLite
    if not export_data_from_sqlite():
        return False
    
    # Importer vers PostgreSQL
    if not import_data_to_postgresql():
        return False
    
    print("🎉 Migration terminée avec succès!")
    print("Vos données sont maintenant dans PostgreSQL!")
    
    return True

if __name__ == '__main__':
    main()
