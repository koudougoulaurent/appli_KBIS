#!/usr/bin/env python
"""
Script de nettoyage et préparation pour la restauration depuis etat2
"""
import os
import shutil
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def clean_current_state():
    """Nettoie l'état actuel pour préparer la restauration"""
    print("🧹 Nettoyage de l'état actuel...")
    
    try:
        # 1. Supprimer les fichiers de migration problématiques
        migration_dirs = [
            'contrats/migrations',
            'paiements/migrations',
            'utilisateurs/migrations',
            'proprietes/migrations'
        ]
        
        for migration_dir in migration_dirs:
            if os.path.exists(migration_dir):
                # Garder __init__.py mais supprimer les autres fichiers
                for file in os.listdir(migration_dir):
                    if file != '__init__.py' and file.endswith('.py'):
                        file_path = os.path.join(migration_dir, file)
                        os.remove(file_path)
                        print(f"🗑️ Supprimé: {file_path}")
        
        # 2. Supprimer la base de données actuelle
        db_file = 'db.sqlite3'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ Supprimé: {db_file}")
        
        # 3. Supprimer les fichiers de cache Python
        cache_dirs = ['__pycache__', '.pytest_cache']
        for root, dirs, files in os.walk('.'):
            for dir_name in dirs:
                if dir_name in cache_dirs:
                    cache_path = os.path.join(root, dir_name)
                    shutil.rmtree(cache_path)
                    print(f"🗑️ Supprimé: {cache_path}")
        
        print("✅ Nettoyage terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

def prepare_for_restore():
    """Prépare l'environnement pour la restauration"""
    print("\n🔧 Préparation pour la restauration...")
    
    try:
        # 1. Créer les dossiers de migration s'ils n'existent pas
        migration_dirs = [
            'contrats/migrations',
            'paiements/migrations',
            'utilisateurs/migrations',
            'proprietes/migrations'
        ]
        
        for migration_dir in migration_dirs:
            os.makedirs(migration_dir, exist_ok=True)
            init_file = os.path.join(migration_dir, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    pass
                print(f"📁 Créé: {init_file}")
        
        print("✅ Préparation terminée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la préparation: {e}")
        return False

def check_etat2_backup():
    """Vérifie si le backup etat2 existe"""
    print("\n🔍 Recherche du backup etat2...")
    
    possible_locations = [
        'etat2',
        'backup/etat2',
        'etat2.zip',
        'backup/etat2.zip',
        '../etat2',
        '../backup/etat2'
    ]
    
    found_backups = []
    for location in possible_locations:
        if os.path.exists(location):
            found_backups.append(location)
            print(f"✅ Trouvé: {location}")
    
    if not found_backups:
        print("❌ Aucun backup etat2 trouvé")
        print("\n📋 Emplacements vérifiés:")
        for location in possible_locations:
            print(f"   - {location}")
        print("\n💡 Veuillez indiquer où se trouve votre backup etat2")
        return None
    
    return found_backups

def restore_from_etat2(backup_path):
    """Restaure depuis le backup etat2"""
    print(f"\n🔄 Restauration depuis {backup_path}...")
    
    try:
        if backup_path.endswith('.zip'):
            # Restauration depuis un fichier ZIP
            import zipfile
            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                zip_ref.extractall('.')
            print("✅ Restauration ZIP terminée")
            
        elif os.path.isdir(backup_path):
            # Restauration depuis un dossier
            # Copier les fichiers importants
            important_files = [
                'db.sqlite3',
                'manage.py',
                'requirements.txt'
            ]
            
            for file_name in important_files:
                src = os.path.join(backup_path, file_name)
                if os.path.exists(src):
                    shutil.copy2(src, '.')
                    print(f"📄 Copié: {file_name}")
            
            # Copier les dossiers d'applications
            app_dirs = ['core', 'utilisateurs', 'proprietes']
            for app_dir in app_dirs:
                src = os.path.join(backup_path, app_dir)
                if os.path.exists(src):
                    if os.path.exists(app_dir):
                        shutil.rmtree(app_dir)
                    shutil.copytree(src, app_dir)
                    print(f"📁 Copié: {app_dir}")
            
            print("✅ Restauration dossier terminée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {e}")
        return False

def main():
    """Fonction principale"""
    print("🏢 RESTAURATION DEPUIS BACKUP ETAT2")
    print("=" * 50)
    
    # 1. Nettoyer l'état actuel
    if not clean_current_state():
        print("❌ Échec du nettoyage")
        return
    
    # 2. Préparer pour la restauration
    if not prepare_for_restore():
        print("❌ Échec de la préparation")
        return
    
    # 3. Chercher le backup etat2
    backups = check_etat2_backup()
    if not backups:
        print("\n❌ Impossible de continuer sans backup")
        return
    
    # 4. Restaurer depuis le premier backup trouvé
    backup_path = backups[0]
    if restore_from_etat2(backup_path):
        print("\n🎉 Restauration terminée avec succès !")
        print("\n📋 Prochaines étapes:")
        print("1. python manage.py migrate")
        print("2. python manage.py createsuperuser")
        print("3. python manage.py runserver")
        print("\n🌐 Accès:")
        print("- Admin: http://127.0.0.1:8000/admin/")
    else:
        print("\n❌ Échec de la restauration")

if __name__ == '__main__':
    main() 