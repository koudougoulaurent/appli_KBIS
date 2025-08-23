import os
import shutil
from datetime import datetime

def sauvegarder_etat17():
    """Sauvegarde l'état actuel du projet sous le nom etat17"""
    
    # Créer le nom du répertoire de sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"etat17_{timestamp}"
    backup_path = os.path.join("backups", backup_name)
    
    # Créer le répertoire de sauvegarde s'il n'existe pas
    os.makedirs("backups", exist_ok=True)
    
    # Copier l'ensemble du projet
    try:
        shutil.copytree(".", backup_path, 
                       ignore=shutil.ignore_patterns(
                           "__pycache__", "*.pyc", ".git", "backups", 
                           "venv", "*.log", "*.sqlite3", "media", 
                           "staticfiles", ".vscode", ".idea"
                       ))
        print(f"Sauvegarde créée avec succès : {backup_path}")
        
        # Créer un fichier de métadonnées
        metadata = {
            "name": "etat17",
            "timestamp": timestamp,
            "description": "Sauvegarde de l'état 17 avec dashboards dynamiques et corrections de bugs"
        }
        
        with open(os.path.join(backup_path, "metadata_etat17.json"), "w") as f:
            import json
            json.dump(metadata, f, indent=2)
            
        print("Fichier de métadonnées créé")
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")

if __name__ == "__main__":
    sauvegarder_etat17()