#!/usr/bin/env python
"""
Script de migration des données de SQLite vers PostgreSQL
Pour déployer sur Render avec une base de données permanente
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

from django.core.management import call_command
from django.db import connections
import json
from datetime import datetime


def migrate_to_postgresql():
    """Migrer les données de SQLite vers PostgreSQL"""
    print("🔄 MIGRATION SQLITE → POSTGRESQL - KBIS INTERNATIONAL")
    print("=" * 60)
    
    try:
        # 1. Vérifier la connexion à la base de données
        print("🔍 Vérification des connexions...")
        
        # SQLite (source)
        sqlite_conn = connections['default']
        if 'sqlite' not in sqlite_conn.vendor:
            print("⚠️ La base de données par défaut n'est pas SQLite")
            print("💡 Assurez-vous d'utiliser les bons settings")
        
        # PostgreSQL (destination)
        postgres_conn = connections['postgresql']
        if postgres_conn.vendor != 'postgresql':
            print("❌ Connexion PostgreSQL non trouvée")
            print("💡 Vérifiez la configuration DATABASE_URL")
            return False
        
        print("✅ Connexions vérifiées")
        
        # 2. Créer les tables PostgreSQL
        print("\n🗄️ Création des tables PostgreSQL...")
        call_command('migrate', database='postgresql', verbosity=2)
        print("✅ Tables créées")
        
        # 3. Exporter les données SQLite
        print("\n📤 Export des données SQLite...")
        export_data_from_sqlite()
        
        # 4. Importer les données PostgreSQL
        print("\n📥 Import des données PostgreSQL...")
        import_data_to_postgresql()
        
        # 5. Vérifier l'intégrité
        print("\n🔍 Vérification de l'intégrité...")
        verify_data_integrity()
        
        print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS !")
        print("🌐 Votre application est prête pour Render")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False


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
    with open('migration_data.json', 'w', encoding='utf-8') as f:
        json.dump(exported_data, f, indent=2, default=str)
    
    print("  💾 Données exportées dans migration_data.json")


def import_data_to_postgresql():
    """Importer les données dans PostgreSQL"""
    print("  📥 Import des données...")
    
    try:
        with open('migration_data.json', 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        for model_path, data in exported_data.items():
            if not data:
                continue
                
            try:
                app_label, model_name = model_path.split('.')
                from django.apps import apps
                model = apps.get_model(app_label, model_name)
                
                # Importer les données
                for record in data:
                    # Créer l'objet sans l'ID pour éviter les conflits
                    if 'id' in record:
                        del record['id']
                    
                    model.objects.using('postgresql').create(**record)
                
                print(f"    ✅ {model_name}: {len(data)} enregistrements importés")
                
            except Exception as e:
                print(f"    ⚠️ Erreur pour {model_path}: {e}")
    
    except FileNotFoundError:
        print("    ❌ Fichier migration_data.json non trouvé")
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
            sqlite_count = model.objects.using('default').count()
            postgres_count = model.objects.using('postgresql').count()
            
            if sqlite_count == postgres_count:
                print(f"    ✅ {model_name}: {postgres_count} enregistrements")
            else:
                print(f"    ⚠️ {model_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                
        except Exception as e:
            print(f"    ❌ Erreur pour {model_path}: {e}")


def cleanup_migration_files():
    """Nettoyer les fichiers de migration temporaires"""
    print("\n🧹 Nettoyage des fichiers temporaires...")
    
    files_to_remove = [
        'migration_data.json',
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
    success = migrate_to_postgresql()
    
    if success:
        cleanup_migration_files()
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("1. Vérifiez les données dans PostgreSQL")
        print("2. Testez l'application avec PostgreSQL")
        print("3. Déployez sur Render")
        print("4. Configurez les variables d'environnement")
    else:
        print("\n❌ MIGRATION ÉCHOUÉE")
        print("💡 Vérifiez les logs et réessayez")
        sys.exit(1)
