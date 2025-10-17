#!/usr/bin/env python
"""
Script de migration des données de SQLite vers PostgreSQL
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configuration Django pour SQLite
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def export_sqlite_data():
    """Exporte les données de SQLite vers des fichiers JSON"""
    print("EXPORT DES DONNEES SQLITE")
    print("=" * 40)
    
    try:
        # Export des données principales
        apps_to_export = [
            'core',
            'utilisateurs', 
            'proprietes',
            'contrats',
            'paiements',
            'notifications'
        ]
        
        for app in apps_to_export:
            print(f"Export de {app}...")
            execute_from_command_line([
                'manage.py', 'dumpdata', app, 
                '--indent', '2',
                '--output', f'data_export_{app}.json'
            ])
            print(f"  OK {app}")
        
        print("Export termine avec succes!")
        return True
        
    except Exception as e:
        print(f"Erreur export: {e}")
        return False

def test_postgresql_connection():
    """Test la connexion PostgreSQL"""
    print("\nTEST CONNEXION POSTGRESQL")
    print("=" * 40)
    
    try:
        # Changer vers la configuration PostgreSQL
        os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_postgresql'
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"Connexion PostgreSQL reussie!")
            print(f"Version: {version[0]}")
        
        return True
        
    except Exception as e:
        print(f"Erreur connexion PostgreSQL: {e}")
        return False

def create_postgresql_schema():
    """Crée le schéma PostgreSQL"""
    print("\nCREATION SCHEMA POSTGRESQL")
    print("=" * 40)
    
    try:
        # Appliquer les migrations
        execute_from_command_line(['manage.py', 'migrate'])
        print("Migrations appliquees avec succes!")
        
        # Créer un superutilisateur
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@kbis-immobilier.com',
                password='admin123',
                first_name='Admin',
                last_name='KBIS'
            )
            print("Superutilisateur cree: admin/admin123")
        else:
            print("Superutilisateur existe deja")
        
        return True
        
    except Exception as e:
        print(f"Erreur creation schema: {e}")
        return False

def import_data_to_postgresql():
    """Importe les données dans PostgreSQL"""
    print("\nIMPORT DES DONNEES VERS POSTGRESQL")
    print("=" * 40)
    
    try:
        apps_to_import = [
            'core',
            'utilisateurs', 
            'proprietes',
            'contrats',
            'paiements',
            'notifications'
        ]
        
        for app in apps_to_import:
            json_file = f'data_export_{app}.json'
            if os.path.exists(json_file):
                print(f"Import de {app}...")
                execute_from_command_line([
                    'manage.py', 'loaddata', json_file
                ])
                print(f"  OK {app}")
            else:
                print(f"  Fichier {json_file} non trouve")
        
        print("Import termine avec succes!")
        return True
        
    except Exception as e:
        print(f"Erreur import: {e}")
        return False

def main():
    """Fonction principale"""
    print("MIGRATION SQLITE VERS POSTGRESQL")
    print("=" * 50)
    
    # Étape 1: Export SQLite
    if not export_sqlite_data():
        print("Echec de l'export SQLite")
        return False
    
    # Étape 2: Test connexion PostgreSQL
    if not test_postgresql_connection():
        print("Echec de la connexion PostgreSQL")
        return False
    
    # Étape 3: Créer le schéma PostgreSQL
    if not create_postgresql_schema():
        print("Echec de la creation du schema PostgreSQL")
        return False
    
    # Étape 4: Importer les données
    if not import_data_to_postgresql():
        print("Echec de l'import des donnees")
        return False
    
    print("\nMIGRATION TERMINEE AVEC SUCCES!")
    print("Votre application est maintenant sur PostgreSQL!")
    return True

if __name__ == '__main__':
    main()
