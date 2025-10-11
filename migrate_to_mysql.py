#!/usr/bin/env python
"""
Script de migration des données de SQLite vers MySQL
Pour l'application KBIS Immobilier
"""
import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')

# Initialiser Django
django.setup()

from django.core.management import call_command
from django.db import connections
from django.conf import settings
import json

def export_data_from_sqlite():
    """Exporter toutes les données de SQLite vers des fichiers JSON"""
    print("📤 Export des données depuis SQLite...")
    
    # Liste des modèles à exporter
    models_to_export = [
        'auth.User',
        'utilisateurs.Utilisateur',
        'utilisateurs.Groupetravail',
        'core.Configurationentreprise',
        'core.Devise',
        'core.Templaterecu',
        'core.Auditlog',
        'core.Logaudit',
        'proprietes.Typebien',
        'proprietes.Chargesbailleur',
        'proprietes.Bailleur',
        'proprietes.Locataire',
        'proprietes.Propriete',
        'proprietes.Piece',
        'proprietes.Unite',
        'proprietes.Photo',
        'proprietes.Document',
        'contrats.Contrat',
        'paiements.Paiement',
        'paiements.Recu',
        'paiements.Tableaubordfinancier',
        'paiements.Paiementcautionavance',
        'paiements.Chargedeductible',
        'paiements.Quittancepaiement',
        'paiements.Retraitbailleur',
        'paiements.Recapmensuel',
        'paiements.Recapitulatifmensuelbailleur',
        'paiements.Recurecapitulatif',
        'paiements.Detailretraitunite',
        'paiements.Echelonpaiement',
        'paiements.Paiementpartiel',
        'paiements.Avanceloyer',
        'paiements.Consommationavance',
        'notifications.Notification',
        'notifications.Smsnotification',
    ]
    
    # Créer le répertoire d'export
    export_dir = BASE_DIR / 'backup_data'
    export_dir.mkdir(exist_ok=True)
    
    # Exporter chaque modèle
    for model_name in models_to_export:
        try:
            print(f"  Export de {model_name}...")
            call_command('dumpdata', model_name, 
                        output=str(export_dir / f'{model_name.replace(".", "_")}.json'),
                        indent=2)
        except Exception as e:
            print(f"  ⚠️  Erreur lors de l'export de {model_name}: {e}")
    
    print("✅ Export terminé!")

def create_mysql_database():
    """Créer la base de données MySQL"""
    print("🗄️  Création de la base de données MySQL...")
    
    # Configuration MySQL
    mysql_config = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kbis_immobilier',
        'USER': 'kbis_user',
        'PASSWORD': 'kbis_password_2024!',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
    
    # Tester la connexion MySQL
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Connexion MySQL réussie!")
    except Exception as e:
        print(f"❌ Erreur de connexion MySQL: {e}")
        return False
    
    return True

def migrate_to_mysql():
    """Migrer vers MySQL"""
    print("🔄 Migration vers MySQL...")
    
    # Changer les paramètres Django pour MySQL
    os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_production'
    
    # Recharger Django avec les nouveaux paramètres
    django.setup()
    
    try:
        # Appliquer les migrations
        print("  Application des migrations...")
        call_command('migrate', verbosity=2)
        
        # Charger les données
        print("  Chargement des données...")
        backup_dir = BASE_DIR / 'backup_data'
        
        if backup_dir.exists():
            for json_file in backup_dir.glob('*.json'):
                try:
                    print(f"    Chargement de {json_file.name}...")
                    call_command('loaddata', str(json_file))
                except Exception as e:
                    print(f"    ⚠️  Erreur lors du chargement de {json_file.name}: {e}")
        
        print("✅ Migration terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False

def verify_migration():
    """Vérifier que la migration s'est bien passée"""
    print("🔍 Vérification de la migration...")
    
    try:
        from django.db import connection
        from django.contrib.auth.models import User
        from utilisateurs.models import Utilisateur
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            user_count = cursor.fetchone()[0]
            print(f"  Utilisateurs: {user_count}")
            
            cursor.execute("SELECT COUNT(*) FROM core_configurationentreprise")
            config_count = cursor.fetchone()[0]
            print(f"  Configurations: {config_count}")
            
            cursor.execute("SELECT COUNT(*) FROM proprietes_propriete")
            propriete_count = cursor.fetchone()[0]
            print(f"  Propriétés: {propriete_count}")
            
            cursor.execute("SELECT COUNT(*) FROM contrats_contrat")
            contrat_count = cursor.fetchone()[0]
            print(f"  Contrats: {contrat_count}")
            
            cursor.execute("SELECT COUNT(*) FROM paiements_paiement")
            paiement_count = cursor.fetchone()[0]
            print(f"  Paiements: {paiement_count}")
        
        print("✅ Vérification terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Migration KBIS Immobilier: SQLite → MySQL")
    print("=" * 50)
    
    # Étape 1: Exporter les données
    export_data_from_sqlite()
    
    # Étape 2: Vérifier MySQL
    if not create_mysql_database():
        print("❌ Impossible de se connecter à MySQL. Arrêt du script.")
        return
    
    # Étape 3: Migrer
    if migrate_to_mysql():
        # Étape 4: Vérifier
        verify_migration()
        print("\n🎉 Migration terminée avec succès!")
        print("L'application est maintenant prête pour la production avec MySQL.")
    else:
        print("\n❌ La migration a échoué. Vérifiez les logs ci-dessus.")

if __name__ == '__main__':
    main()
