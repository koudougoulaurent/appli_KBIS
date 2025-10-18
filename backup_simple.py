#!/usr/bin/env python
"""
Script de sauvegarde simple avant grandes mises à jour
"""
import os
import shutil
import subprocess
from datetime import datetime

def create_backup():
    """Crée une sauvegarde simple du projet"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"BACKUP_AVANT_MAJ_{timestamp}"
    
    print(f"Creation de la sauvegarde : {backup_dir}")
    print("=" * 60)
    
    try:
        # Créer le dossier de sauvegarde
        os.makedirs(backup_dir, exist_ok=True)
        
        # Sauvegarder les fichiers importants
        important_files = [
            'paiements/',
            'proprietes/',
            'contrats/',
            'core/',
            'utilisateurs/',
            'notifications/',
            'templates/',
            'static/',
            'gestion_immobiliere/',
            'requirements.txt',
            'render.yaml',
            'Procfile',
            'manage.py',
            'emergency_fix.py',
            'db.sqlite3',
        ]
        
        for item in important_files:
            if os.path.exists(item):
                if os.path.isdir(item):
                    # Copier le dossier
                    dst = os.path.join(backup_dir, item)
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                    print(f"  Dossier copie : {item}")
                else:
                    # Copier le fichier
                    dst = os.path.join(backup_dir, item)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(item, dst)
                    print(f"  Fichier copie : {item}")
        
        # Obtenir les informations Git
        try:
            commit_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
            branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()
        except:
            commit_hash = "unknown"
            branch = "unknown"
        
        # Créer un fichier d'informations
        info_content = f"""SAUVEGARDE AVANT GRANDES MISES A JOUR
=====================================
Date: {timestamp}
Commit: {commit_hash}
Branche: {branch}
Description: Sauvegarde avant grandes mises à jour
- Système de recherche amélioré complet
- Correction logique caution vs avance
- Configuration PostgreSQL prête pour Render

FICHIERS SAUVEGARDES:
- Tous les fichiers Python des apps
- Templates HTML
- Fichiers de configuration
- Base de données SQLite
- Migrations

POUR RESTAURER:
1. Copier le contenu de ce dossier vers le projet
2. Ou utiliser git checkout du commit {commit_hash}
"""
        
        with open(os.path.join(backup_dir, 'README_SAUVEGARDE.txt'), 'w', encoding='utf-8') as f:
            f.write(info_content)
        
        print("\n" + "=" * 60)
        print("SAUVEGARDE COMPLETE TERMINEE !")
        print(f"Dossier : {backup_dir}")
        print(f"Commit : {commit_hash}")
        print(f"Branche : {branch}")
        print("=" * 60)
        
        return backup_dir
        
    except Exception as e:
        print(f"ERREUR lors de la sauvegarde : {e}")
        return None

if __name__ == '__main__':
    backup_dir = create_backup()
    if backup_dir:
        print(f"\nPour restaurer plus tard : copier le contenu de {backup_dir}/")
        print("Sauvegarde securisee et prete pour les grandes mises a jour !")
    else:
        print("Echec de la sauvegarde")