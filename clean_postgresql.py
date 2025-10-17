#!/usr/bin/env python
"""
Script pour nettoyer complètement la base PostgreSQL
"""
import os
import sys
import django

# Configuration Django pour PostgreSQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

from django.db import connection

def clean_postgresql_database():
    """Nettoie complètement la base PostgreSQL"""
    print("NETTOYAGE COMPLET DE LA BASE POSTGRESQL")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            # 1. Lister toutes les tables
            print("1. Identification des tables existantes...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Tables trouvées: {len(tables)}")
            
            if not tables:
                print("   Aucune table à supprimer. La base est déjà vide.")
                return True
            
            # 2. Désactiver les contraintes de clés étrangères
            print("2. Désactivation des contraintes...")
            cursor.execute("SET session_replication_role = 'replica';")
            
            # 3. Supprimer toutes les tables
            print("3. Suppression de toutes les tables...")
            for table in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                print(f"   OK Table {table} supprimée")
            
            # 4. Réactiver les contraintes
            print("4. Réactivation des contraintes...")
            cursor.execute("SET session_replication_role = 'origin';")
            
            # 5. Supprimer les séquences orphelines
            print("5. Nettoyage des séquences...")
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public'
            """)
            sequences = [row[0] for row in cursor.fetchall()]
            for seq in sequences:
                cursor.execute(f'DROP SEQUENCE IF EXISTS "{seq}" CASCADE;')
                print(f"   OK Séquence {seq} supprimée")
            
            print("✅ Base PostgreSQL complètement nettoyée!")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

def apply_migrations():
    """Applique toutes les migrations"""
    print("\nAPPLICATION DES MIGRATIONS")
    print("=" * 50)
    
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations appliquées avec succès!")
        return True
    except Exception as e:
        print(f"❌ Erreur migrations: {e}")
        return False

def create_superuser():
    """Crée un superutilisateur"""
    print("\nCRÉATION DU SUPERUTILISATEUR")
    print("=" * 50)
    
    try:
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
            print("✅ Superutilisateur créé: admin/admin123")
        else:
            print("ℹ️ Superutilisateur 'admin' existe déjà")
        
        return True
    except Exception as e:
        print(f"❌ Erreur superutilisateur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 MIGRATION POSTGRESQL PROPRE")
    print("=" * 60)
    
    if not clean_postgresql_database():
        print("❌ Échec du nettoyage de la base")
        sys.exit(1)
    
    if not apply_migrations():
        print("❌ Échec des migrations")
        sys.exit(1)
    
    if not create_superuser():
        print("❌ Échec de la création du superutilisateur")
        sys.exit(1)
    
    print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
    print("✅ Base PostgreSQL nettoyée")
    print("✅ Migrations appliquées")
    print("✅ Superutilisateur créé")
    print("\nVotre application est maintenant prête sur PostgreSQL!")

if __name__ == '__main__':
    main()
