#!/usr/bin/env python
"""
Script de sauvegarde automatique pour Render
Sauvegarde la base de données avant chaque redéploiement
"""

import os
import sys
import django
from datetime import datetime
import subprocess
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings
from django.db import connection

def create_backup():
    """Crée une sauvegarde de la base de données"""
    print("🔄 Création de la sauvegarde...")
    
    # Créer le dossier de sauvegarde
    backup_dir = os.path.join(settings.BASE_DIR, 'backup_data')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nom du fichier de sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"backup_render_{timestamp}.json")
    
    try:
        # Sauvegarde des données
        with open(backup_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', '--natural-foreign', '--natural-primary', stdout=f)
        
        print(f"✅ Sauvegarde créée: {backup_file}")
        
        # Créer un fichier de métadonnées
        metadata = {
            'timestamp': timestamp,
            'database': settings.DATABASES['default']['NAME'],
            'engine': settings.DATABASES['default']['ENGINE'],
            'file_size': os.path.getsize(backup_file),
            'created_at': datetime.now().isoformat()
        }
        
        metadata_file = os.path.join(backup_dir, f"metadata_{timestamp}.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Métadonnées créées: {metadata_file}")
        
        return backup_file, metadata_file
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return None, None

def restore_backup():
    """Restaure la dernière sauvegarde"""
    print("🔄 Restauration de la sauvegarde...")
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backup_data')
    
    if not os.path.exists(backup_dir):
        print("❌ Aucun dossier de sauvegarde trouvé")
        return False
    
    # Trouver le dernier fichier de sauvegarde
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_render_') and f.endswith('.json')]
    
    if not backup_files:
        print("❌ Aucun fichier de sauvegarde trouvé")
        return False
    
    # Trier par date de modification
    backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
    latest_backup = os.path.join(backup_dir, backup_files[0])
    
    try:
        # Restaurer les données
        call_command('loaddata', latest_backup)
        print(f"✅ Sauvegarde restaurée: {latest_backup}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {e}")
        return False

def check_database_connection():
    """Vérifie la connexion à la base de données"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Connexion à la base de données OK")
            return True
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Script de sauvegarde Render")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier la connexion
    if not check_database_connection():
        print("❌ Impossible de se connecter à la base de données")
        return
    
    # Vérifier si on est sur Render
    if os.environ.get('RENDER'):
        print("🌐 Environnement Render détecté")
        
        # Créer une sauvegarde
        backup_file, metadata_file = create_backup()
        
        if backup_file:
            print("✅ Sauvegarde terminée avec succès")
        else:
            print("❌ Échec de la sauvegarde")
    else:
        print("💻 Environnement local détecté")
        
        # En local, on peut restaurer si nécessaire
        if len(sys.argv) > 1 and sys.argv[1] == 'restore':
            restore_backup()

if __name__ == '__main__':
    main()
