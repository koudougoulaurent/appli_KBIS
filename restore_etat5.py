#!/usr/bin/env python
"""
Script de restauration pour l'état 5 de l'application de gestion immobilière
Date: 20 juillet 2025
Description: Restaure l'état 5 avec toutes les fonctionnalités complètes
"""

import os
import shutil
import zipfile
from datetime import datetime

def restaurer_etat5():
    """Restaure l'état 5 de l'application"""
    
    print("🔄 Début de la restauration de l'état 5")
    
    # Nom de la sauvegarde à restaurer
    nom_sauvegarde = "etat5"
    timestamp = "20250720_085554"  # Timestamp de la sauvegarde
    nom_dossier = f"backups/{nom_sauvegarde}_{timestamp}"
    nom_archive = f"{nom_dossier}.zip"
    
    print(f"📁 Source: {nom_dossier}")
    print(f"📦 Archive: {nom_archive}")
    
    try:
        # Vérifier si la sauvegarde existe
        if not os.path.exists(nom_dossier) and not os.path.exists(nom_archive):
            print(f"❌ Erreur: Sauvegarde {nom_sauvegarde} non trouvée")
            return False
        
        # Si l'archive existe mais pas le dossier, extraire l'archive
        if os.path.exists(nom_archive) and not os.path.exists(nom_dossier):
            print("📦 Extraction de l'archive...")
            with zipfile.ZipFile(nom_archive, 'r') as zipf:
                zipf.extractall("backups/")
            print("✅ Archive extraite")
        
        # Créer une sauvegarde de l'état actuel avant restauration
        backup_actuel = f"backups/backup_avant_restauration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 Sauvegarde de l'état actuel: {backup_actuel}")
        
        # Éléments à sauvegarder avant restauration
        elements_a_sauvegarder = [
            'proprietes', 'contrats', 'paiements', 'utilisateurs', 'core', 'notifications',
            'gestion_immobiliere', 'templates', 'static', 'manage.py', 'db.sqlite3'
        ]
        
        os.makedirs(backup_actuel, exist_ok=True)
        for element in elements_a_sauvegarder:
            if os.path.exists(element):
                if os.path.isdir(element):
                    shutil.copytree(element, os.path.join(backup_actuel, element), dirs_exist_ok=True)
                else:
                    shutil.copy2(element, backup_actuel)
        
        print("✅ Sauvegarde de l'état actuel créée")
        
        # Éléments à restaurer
        elements_a_restaurer = [
            'proprietes',
            'contrats', 
            'paiements',
            'utilisateurs',
            'core',
            'notifications',
            'gestion_immobiliere',
            'templates',
            'static',
            'manage.py',
            'db.sqlite3',
            'requirements.txt',
            'README.md',
            'API_DOCUMENTATION.md',
            'SECURITE_FORMULAIRES_COMPLETE.md',
            'init_data.py',
            'init_basic_data.py',
            'create_tables.py',
            'clean_and_restore.py',
            'create_missing_templates.py',
        ]
        
        print("🔄 Restauration des fichiers...")
        
        # Supprimer les éléments existants
        for element in elements_a_restaurer:
            if os.path.exists(element):
                if os.path.isdir(element):
                    shutil.rmtree(element)
                else:
                    os.remove(element)
                print(f"🗑️  Supprimé: {element}")
        
        # Copier les éléments depuis la sauvegarde
        for element in elements_a_restaurer:
            source = os.path.join(nom_dossier, element)
            if os.path.exists(source):
                if os.path.isdir(source):
                    shutil.copytree(source, element)
                    print(f"📁 Dossier restauré: {element}")
                else:
                    shutil.copy2(source, element)
                    print(f"📄 Fichier restauré: {element}")
            else:
                print(f"⚠️  Élément non trouvé dans la sauvegarde: {element}")
        
        # Créer un fichier de confirmation de restauration
        confirmation = f"""# Confirmation de Restauration - État 5

## Informations de restauration
- **Date de restauration**: {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}
- **État restauré**: {nom_sauvegarde}
- **Sauvegarde source**: {nom_dossier}
- **Backup de l'état précédent**: {backup_actuel}

## Fonctionnalités restaurées

### ✅ Gestion des propriétés
- Liste des propriétés avec filtres
- Ajout de nouvelles propriétés
- **Modification des propriétés** (NOUVEAU)
- Détail complet des propriétés

### ✅ Gestion des bailleurs
- Liste des bailleurs avec statistiques
- Ajout de nouveaux bailleurs
- Modification des informations
- Détail complet avec propriétés

### ✅ Gestion des locataires
- Liste des locataires
- Ajout de nouveaux locataires
- Modification des informations
- Détail complet avec contrats

### ✅ Système de charges bailleur
- Gestion complète des charges
- Déduction du loyer
- Remboursement des charges
- Interface dédiée

### ✅ Interface utilisateur
- Design moderne Bootstrap 5
- Templates responsives
- Validation en temps réel
- Navigation intuitive

## Fichiers restaurés
{chr(10).join(f"- {element}" for element in elements_a_restaurer if os.path.exists(element))}

## Prochaines étapes
1. Vérifier que l'application fonctionne: `python manage.py runserver`
2. Tester les fonctionnalités principales
3. Vérifier la base de données

---
**Restauration effectuée le {datetime.now().strftime("%d/%m/%Y à %H:%M:%S")}**
"""
        
        with open("RESTAURATION_ETAT5_CONFIRMATION.md", 'w', encoding='utf-8') as f:
            f.write(confirmation)
        
        print("📝 Fichier de confirmation créé: RESTAURATION_ETAT5_CONFIRMATION.md")
        
        # Instructions post-restauration
        print(f"\n🎉 RESTAURATION DE L'ÉTAT 5 TERMINÉE AVEC SUCCÈS!")
        print(f"📁 État précédent sauvegardé: {backup_actuel}")
        print(f"📝 Confirmation: RESTAURATION_ETAT5_CONFIRMATION.md")
        
        print(f"\n📋 PROCHAINES ÉTAPES:")
        print(f"1. Démarrer le serveur: python manage.py runserver")
        print(f"2. Tester les fonctionnalités:")
        print(f"   - Liste des propriétés: http://127.0.0.1:8000/proprietes/")
        print(f"   - Liste des bailleurs: http://127.0.0.1:8000/proprietes/bailleurs/")
        print(f"   - Liste des locataires: http://127.0.0.1:8000/proprietes/locataires/")
        print(f"3. Vérifier la modification de propriétés depuis la page d'un bailleur")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {str(e)}")
        return False

if __name__ == "__main__":
    restaurer_etat5() 