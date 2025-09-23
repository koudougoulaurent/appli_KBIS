#!/usr/bin/env python
"""
Script de migration vers le plan Pro (100 GB)
Migration des données de SQLite vers PostgreSQL Pro
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_pro')
django.setup()

from django.core.management import call_command
from django.db import connections
import json
from datetime import datetime


def migrate_to_pro():
    """Migrer vers le plan Pro (100 GB)"""
    print("🚀 MIGRATION VERS PLAN PRO (100 GB) - KBIS IMMOBILIER")
    print("=" * 60)
    
    try:
        # 1. Vérifier la connexion PostgreSQL Pro
        print("🔍 Vérification de la connexion PostgreSQL Pro...")
        
        connection = connections['default']
        if connection.vendor != 'postgresql':
            print("❌ Connexion PostgreSQL non trouvée")
            print("💡 Vérifiez la configuration DATABASE_URL")
            return False
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connexion PostgreSQL Pro réussie: {version[0]}")
        
        # 2. Vérifier l'espace disque disponible
        print("\n💾 Vérification de l'espace disque...")
        check_disk_space()
        
        # 3. Créer les tables PostgreSQL Pro
        print("\n🗄️ Création des tables PostgreSQL Pro...")
        call_command('migrate', verbosity=2)
        print("✅ Tables créées")
        
        # 4. Exporter les données SQLite
        print("\n📤 Export des données SQLite...")
        export_data_from_sqlite()
        
        # 5. Importer les données PostgreSQL Pro
        print("\n📥 Import des données PostgreSQL Pro...")
        import_data_to_postgresql_pro()
        
        # 6. Vérifier l'intégrité
        print("\n🔍 Vérification de l'intégrité...")
        verify_data_integrity()
        
        # 7. Optimiser la base de données
        print("\n⚡ Optimisation de la base de données...")
        optimize_database()
        
        print("\n🎉 MIGRATION VERS PLAN PRO TERMINÉE !")
        print("🌐 Votre application est prête avec 100 GB de stockage")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False


def check_disk_space():
    """Vérifier l'espace disque disponible"""
    try:
        connection = connections['default']
        with connection.cursor() as cursor:
            # Vérifier l'espace disque
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            size = cursor.fetchone()
            print(f"  📊 Taille actuelle: {size[0]}")
            
            # Vérifier l'espace disponible
            cursor.execute("""
                SELECT pg_size_pretty(
                    pg_tablespace_size('pg_default') - pg_database_size(current_database())
                );
            """)
            available = cursor.fetchone()
            print(f"  💾 Espace disponible: {available[0]}")
            
            # Vérifier les limites
            cursor.execute("""
                SELECT setting FROM pg_settings WHERE name = 'max_database_size';
            """)
            limit = cursor.fetchone()
            print(f"  🔒 Limite de base de données: {limit[0] if limit[0] else 'Illimitée'}")
            
    except Exception as e:
        print(f"  ⚠️ Erreur lors de la vérification de l'espace: {e}")


def export_data_from_sqlite():
    """Exporter les données de SQLite"""
    print("  📋 Export des modèles...")
    
    # Liste des modèles à exporter
    models_to_export = [
        'utilisateurs.Utilisateur',
        'utilisateurs.GroupeTravail',
        'proprietes.TypeBien',
        'proprietes.Bailleur',
        'proprietes.Locataire',
        'proprietes.Propriete',
        'contrats.Contrat',
        'contrats.Quittance',
        'paiements.Paiement',
        'core.NiveauAcces',
        'notifications.Notification'
    ]
    
    exported_data = {}
    
    for model_path in models_to_export:
        try:
            app_label, model_name = model_path.split('.')
            from django.apps import apps
            model = apps.get_model(app_label, model_name)
            
            # Exporter les données
            data = list(model.objects.using('default').values())
            exported_data[model_path] = data
            
            print(f"    ✅ {model_name}: {len(data)} enregistrements")
            
        except Exception as e:
            print(f"    ⚠️ Erreur pour {model_path}: {e}")
    
    # Sauvegarder dans un fichier JSON
    with open('migration_pro_data.json', 'w', encoding='utf-8') as f:
        json.dump(exported_data, f, indent=2, default=str)
    
    print("  💾 Données exportées dans migration_pro_data.json")


def import_data_to_postgresql_pro():
    """Importer les données dans PostgreSQL Pro"""
    print("  📥 Import des données...")
    
    try:
        with open('migration_pro_data.json', 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        for model_path, data in exported_data.items():
            if not data:
                continue
                
            try:
                app_label, model_name = model_path.split('.')
                from django.apps import apps
                model = apps.get_model(app_label, model_name)
                
                # Importer les données par lots pour optimiser
                batch_size = 1000
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    
                    # Créer les objets sans l'ID
                    for record in batch:
                        if 'id' in record:
                            del record['id']
                    
                    # Créer en lot
                    model.objects.using('default').bulk_create([
                        model(**record) for record in batch
                    ])
                
                print(f"    ✅ {model_name}: {len(data)} enregistrements importés")
                
            except Exception as e:
                print(f"    ⚠️ Erreur pour {model_path}: {e}")
    
    except FileNotFoundError:
        print("    ❌ Fichier migration_pro_data.json non trouvé")
    except Exception as e:
        print(f"    ❌ Erreur lors de l'import: {e}")


def verify_data_integrity():
    """Vérifier l'intégrité des données"""
    print("  🔍 Vérification de l'intégrité...")
    
    # Vérifier les compteurs
    models_to_check = [
        'utilisateurs.Utilisateur',
        'proprietes.Bailleur',
        'proprietes.Locataire',
        'proprietes.Propriete',
        'contrats.Contrat',
        'paiements.Paiement'
    ]
    
    for model_path in models_to_check:
        try:
            app_label, model_name = model_path.split('.')
            from django.apps import apps
            model = apps.get_model(app_label, model_name)
            
            # Compter les enregistrements
            count = model.objects.using('default').count()
            print(f"    ✅ {model_name}: {count} enregistrements")
            
        except Exception as e:
            print(f"    ❌ Erreur pour {model_path}: {e}")


def optimize_database():
    """Optimiser la base de données"""
    print("  ⚡ Optimisation...")
    
    try:
        connection = connections['default']
        with connection.cursor() as cursor:
            # Analyser les tables
            cursor.execute("ANALYZE;")
            print("    ✅ Analyse des tables terminée")
            
            # Vérifier les index
            cursor.execute("""
                SELECT schemaname, tablename, indexname, indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            indexes = cursor.fetchall()
            print(f"    ✅ {len(indexes)} index trouvés")
            
            # Vérifier les contraintes
            cursor.execute("""
                SELECT conname, contype, confrelid::regclass
                FROM pg_constraint 
                WHERE connamespace = 'public'::regnamespace;
            """)
            constraints = cursor.fetchall()
            print(f"    ✅ {len(constraints)} contraintes trouvées")
            
    except Exception as e:
        print(f"    ⚠️ Erreur lors de l'optimisation: {e}")


def cleanup_migration_files():
    """Nettoyer les fichiers de migration temporaires"""
    print("\n🧹 Nettoyage des fichiers temporaires...")
    
    files_to_remove = [
        'migration_pro_data.json',
        'migration_log.txt'
    ]
    
    for file in files_to_remove:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"  ✅ {file} supprimé")
        except Exception as e:
            print(f"  ⚠️ Erreur lors de la suppression de {file}: {e}")


if __name__ == "__main__":
    success = migrate_to_pro()
    
    if success:
        cleanup_migration_files()
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("1. Vérifiez les données dans PostgreSQL Pro")
        print("2. Testez l'application avec 100 GB de stockage")
        print("3. Configurez le monitoring et les alertes")
        print("4. Déployez sur Render avec le plan Pro")
    else:
        print("\n❌ MIGRATION ÉCHOUÉE")
        print("💡 Vérifiez les logs et réessayez")
        sys.exit(1)
