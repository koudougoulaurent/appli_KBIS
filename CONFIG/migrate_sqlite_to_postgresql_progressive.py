#!/usr/bin/env python3
"""
Script de migration progressive SQLite vers PostgreSQL
Permet de migrer les données existantes de SQLite vers PostgreSQL
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connections, transaction
from django.conf import settings
import json
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

def test_database_connection():
    """Teste la connexion à la base de données"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Connexion base de données réussie: {result}")
            return True
    except Exception as e:
        print(f"❌ Erreur connexion base de données: {e}")
        return False

def get_database_info():
    """Récupère les informations sur la base de données actuelle"""
    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']
    
    if 'postgresql' in engine:
        db_type = "PostgreSQL"
        db_name = db_config.get('NAME', 'N/A')
    elif 'sqlite' in engine:
        db_type = "SQLite"
        db_name = db_config.get('NAME', 'N/A')
    else:
        db_type = "Autre"
        db_name = db_config.get('NAME', 'N/A')
    
    return db_type, db_name

def backup_sqlite_data():
    """Sauvegarde les données SQLite existantes"""
    print("📦 Sauvegarde des données SQLite...")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Exporter les données en JSON
        output = StringIO()
        call_command('dumpdata', '--natural-foreign', '--natural-primary', stdout=output)
        data = output.getvalue()
        
        # Sauvegarder dans un fichier
        backup_file = f"backup_sqlite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(data)
        
        print(f"✅ Sauvegarde créée: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return None

def create_postgresql_tables():
    """Crée les tables PostgreSQL"""
    print("🏗️ Création des tables PostgreSQL...")
    
    try:
        # Synchroniser la base de données (créer les tables)
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
        print("✅ Tables PostgreSQL créées avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur création tables: {e}")
        return False

def migrate_data_from_sqlite():
    """Migre les données de SQLite vers PostgreSQL"""
    print("🔄 Migration des données SQLite vers PostgreSQL...")
    
    try:
        # Charger les données de sauvegarde
        backup_files = [f for f in os.listdir('.') if f.startswith('backup_sqlite_') and f.endswith('.json')]
        if not backup_files:
            print("❌ Aucun fichier de sauvegarde trouvé")
            return False
        
        # Prendre le plus récent
        latest_backup = max(backup_files)
        print(f"📁 Utilisation de la sauvegarde: {latest_backup}")
        
        # Charger les données
        with open(latest_backup, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filtrer les données pour éviter les conflits
        filtered_data = []
        for item in data:
            # Exclure les données système Django
            if not item['model'].startswith('contenttypes.') and not item['model'].startswith('auth.'):
                filtered_data.append(item)
        
        print(f"📊 {len(filtered_data)} objets à migrer")
        
        # Charger les données dans PostgreSQL
        from django.core.management import call_command
        from io import StringIO
        
        # Convertir en JSON pour loaddata
        json_data = json.dumps(filtered_data)
        input_stream = StringIO(json_data)
        
        # Charger les données
        call_command('loaddata', '--format=json', stdin=input_stream)
        
        print("✅ Données migrées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur migration données: {e}")
        return False

def create_initial_data():
    """Crée les données initiales (groupes, types, etc.)"""
    print("🌱 Création des données initiales...")
    
    try:
        # Exécuter le script de données initiales
        from setup_render import setup_database
        setup_database()
        print("✅ Données initiales créées")
        return True
    except Exception as e:
        print(f"❌ Erreur création données initiales: {e}")
        return False

def main():
    """Fonction principale de migration"""
    print("🚀 MIGRATION PROGRESSIVE SQLITE VERS POSTGRESQL")
    print("=" * 50)
    
    # 1. Tester la connexion
    if not test_database_connection():
        print("❌ Impossible de se connecter à la base de données")
        return False
    
    # 2. Afficher les informations de la base
    db_type, db_name = get_database_info()
    print(f"📊 Base de données actuelle: {db_type} - {db_name}")
    
    # 3. Si c'est SQLite, faire la sauvegarde
    if 'sqlite' in db_type.lower():
        backup_file = backup_sqlite_data()
        if not backup_file:
            print("❌ Échec de la sauvegarde")
            return False
    
    # 4. Créer les tables PostgreSQL
    if not create_postgresql_tables():
        print("❌ Échec de la création des tables")
        return False
    
    # 5. Migrer les données si on vient de SQLite
    if 'sqlite' in db_type.lower():
        if not migrate_data_from_sqlite():
            print("❌ Échec de la migration des données")
            return False
    
    # 6. Créer les données initiales
    if not create_initial_data():
        print("❌ Échec de la création des données initiales")
        return False
    
    # 7. Vérification finale
    if test_database_connection():
        print("🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("✅ Base de données PostgreSQL opérationnelle")
        return True
    else:
        print("❌ Problème lors de la vérification finale")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
