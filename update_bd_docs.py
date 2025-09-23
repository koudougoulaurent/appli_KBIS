#!/usr/bin/env python
"""
Script simple pour mettre à jour la documentation BD
Sans utiliser Django pour éviter l'erreur 'packages'
"""

import os
from datetime import datetime

def update_bd_documentation():
    """Met à jour la documentation BD avec les changements récents"""
    
    print("🔄 Mise à jour de la documentation BD...")
    
    # Lire le fichier README.md existant
    readme_path = "BD/README.md"
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer "KBIS INTERNATIONAL" par "KBIS IMMOBILIER"
        updated_content = content.replace("KBIS INTERNATIONAL", "KBIS IMMOBILIER")
        
        # Ajouter une note de mise à jour
        update_note = f"""
## 📝 Mise à jour - {datetime.now().strftime('%d/%m/%Y %H:%M')}

### Changements récents :
- ✅ Suppression de "INTERNATIONAL" du nom de l'entreprise
- ✅ Remplacement par "KBIS IMMOBILIER" dans toute l'application
- ✅ Ajout du processeur de contexte entreprise_config
- ✅ Mise à jour des templates pour utiliser la configuration dynamique

"""
        
        # Insérer la note de mise à jour après le titre
        lines = updated_content.split('\n')
        if len(lines) > 1:
            lines.insert(2, update_note)
            updated_content = '\n'.join(lines)
        
        # Écrire le fichier mis à jour
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ {readme_path} mis à jour")
    
    # Mettre à jour les autres fichiers de documentation
    files_to_update = [
        "BD/SUMMARY.md",
        "BD/documentation_complete.md",
        "BD/guide_migration.md",
        "BD/diagramme_classes_simple.md",
        "BD/diagramme_cas_utilisation.md"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer "KBIS INTERNATIONAL" par "KBIS IMMOBILIER"
            updated_content = content.replace("KBIS INTERNATIONAL", "KBIS IMMOBILIER")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ {file_path} mis à jour")
    
    # Créer un fichier de changelog
    changelog_path = "BD/CHANGELOG.md"
    changelog_entry = f"""
# 📝 Changelog - Documentation BD

## {datetime.now().strftime('%d/%m/%Y')} - Suppression de "INTERNATIONAL"

### Modifications apportées :
- ✅ Remplacement de "KBIS INTERNATIONAL" par "KBIS IMMOBILIER" dans toute la documentation
- ✅ Mise à jour des templates pour utiliser la configuration dynamique de l'entreprise
- ✅ Ajout du processeur de contexte entreprise_config
- ✅ Modification de la base de données : nom_entreprise = 'KBIS IMMOBILIER'

### Fichiers modifiés :
- `core/context_processors.py` - Ajout du processeur entreprise_config
- `templates/utilisateurs/connexion_groupes.html` - Utilisation de la variable dynamique
- `gestion_immobiliere/settings.py` - Configuration du context processor
- Base de données : `core_configurationentreprise.nom_entreprise`

### Impact :
- L'interface utilisateur affiche maintenant "KBIS IMMOBILIER" au lieu de "KBIS INTERNATIONAL"
- Le nom de l'entreprise est récupéré dynamiquement depuis la configuration
- Plus de cohérence dans l'identité visuelle de l'application

---
*Changelog généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
"""
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(changelog_entry)
    
    print(f"✅ {changelog_path} créé")
    print("🎉 Mise à jour de la documentation BD terminée !")

if __name__ == "__main__":
    update_bd_documentation()
