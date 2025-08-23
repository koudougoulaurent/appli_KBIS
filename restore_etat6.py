#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de restauration pour l'état 6 de l'application de gestion immobilière
Restaure l'application à l'état 6 avec tous les templates de retraits
"""

import os
import shutil
import zipfile
from datetime import datetime

def restore_etat6():
    """Restaure l'application à l'état 6"""
    
    # Configuration
    nom_etat = "etat6"
    timestamp = "20250720_091559"  # Timestamp de l'état 6
    nom_dossier = f"{nom_etat}_{timestamp}"
    chemin_sauvegarde = os.path.join("backups", nom_dossier)
    chemin_zip = os.path.join("backups", f"{nom_dossier}.zip")
    
    # Dossiers à restaurer
    dossiers_a_restaurer = [
        "core",
        "utilisateurs", 
        "proprietes",
        "contrats",
        "paiements",
        "notifications",
        "templates",
        "static",
        "media"
    ]
    
    # Fichiers à restaurer
    fichiers_a_restaurer = [
        "manage.py",
        "db.sqlite3",
        "requirements.txt",
        "README.md"
    ]
    
    try:
        print(f"🔄 Début de la restauration vers l'état {nom_etat}...")
        
        # Vérifier si la sauvegarde existe
        if not os.path.exists(chemin_sauvegarde) and not os.path.exists(chemin_zip):
            print(f"❌ ERREUR : Sauvegarde {nom_etat} non trouvée !")
            print(f"📁 Dossier attendu : {chemin_sauvegarde}")
            print(f"📦 Archive attendue : {chemin_zip}")
            return False
        
        # Créer une sauvegarde de l'état actuel avant restauration
        timestamp_actuel = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_avant_restore = f"backup_avant_restore_etat6_{timestamp_actuel}"
        os.makedirs(os.path.join("backups", backup_avant_restore), exist_ok=True)
        
        print(f"📦 Création d'une sauvegarde de l'état actuel : {backup_avant_restore}")
        
        # Sauvegarder l'état actuel
        for dossier in dossiers_a_restaurer:
            if os.path.exists(dossier):
                shutil.copytree(dossier, os.path.join("backups", backup_avant_restore, dossier), dirs_exist_ok=True)
        
        for fichier in fichiers_a_restaurer:
            if os.path.exists(fichier):
                shutil.copy2(fichier, os.path.join("backups", backup_avant_restore, fichier))
        
        print(f"✅ Sauvegarde de l'état actuel créée : {backup_avant_restore}")
        
        # Extraire l'archive ZIP si nécessaire
        if not os.path.exists(chemin_sauvegarde) and os.path.exists(chemin_zip):
            print(f"📦 Extraction de l'archive : {chemin_zip}")
            with zipfile.ZipFile(chemin_zip, 'r') as zip_ref:
                zip_ref.extractall(os.path.join("backups", nom_dossier))
            print(f"✅ Archive extraite vers : {chemin_sauvegarde}")
        
        # Supprimer les dossiers et fichiers existants
        print("🗑️  Suppression des fichiers existants...")
        
        for dossier in dossiers_a_restaurer:
            if os.path.exists(dossier):
                if os.path.isdir(dossier):
                    shutil.rmtree(dossier)
                else:
                    os.remove(dossier)
                print(f"🗑️  Supprimé : {dossier}")
        
        for fichier in fichiers_a_restaurer:
            if os.path.exists(fichier):
                os.remove(fichier)
                print(f"🗑️  Supprimé : {fichier}")
        
        # Restaurer les dossiers
        print("📁 Restauration des dossiers...")
        for dossier in dossiers_a_restaurer:
            chemin_source = os.path.join(chemin_sauvegarde, dossier)
            if os.path.exists(chemin_source):
                if os.path.isdir(chemin_source):
                    shutil.copytree(chemin_source, dossier)
                    print(f"✅ Dossier restauré : {dossier}")
                else:
                    shutil.copy2(chemin_source, dossier)
                    print(f"✅ Fichier restauré : {dossier}")
            else:
                print(f"⚠️  Dossier/Fichier non trouvé dans la sauvegarde : {dossier}")
        
        # Restaurer les fichiers individuels
        print("📄 Restauration des fichiers...")
        for fichier in fichiers_a_restaurer:
            chemin_source = os.path.join(chemin_sauvegarde, fichier)
            if os.path.exists(chemin_source):
                shutil.copy2(chemin_source, fichier)
                print(f"✅ Fichier restauré : {fichier}")
            else:
                print(f"⚠️  Fichier non trouvé dans la sauvegarde : {fichier}")
        
        # Créer un fichier de confirmation
        confirmation = f"""
RESTAURATION ÉTAT 6 TERMINÉE
============================

Date de restauration : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
État restauré : {nom_etat}
Sauvegarde avant restauration : {backup_avant_restore}

FONCTIONNALITÉS RESTAURÉES :
- ✅ Template de liste des retraits
- ✅ Template de détail de retrait  
- ✅ Template d'ajout de retrait
- ✅ Template de modification de retrait
- ✅ Vue liste_retraits améliorée
- ✅ URLs corrigées pour les retraits
- ✅ Interface moderne et responsive

URLS DISPONIBLES :
- /paiements/retraits/ - Liste des retraits
- /paiements/retraits/ajouter/ - Ajouter un retrait
- /paiements/retraits/detail/<id>/ - Détail d'un retrait
- /paiements/retraits/modifier/<id>/ - Modifier un retrait

Pour démarrer le serveur :
python manage.py runserver

Pour revenir à l'état précédent :
Copier le contenu de backups/{backup_avant_restore} vers le dossier racine
"""
        
        with open("RESTAURATION_ETAT6_CONFIRMEE.txt", 'w', encoding='utf-8') as f:
            f.write(confirmation)
        
        print(f"\n🎉 RESTAURATION TERMINÉE AVEC SUCCÈS !")
        print(f"📁 État restauré : {nom_etat}")
        print(f"📦 Sauvegarde avant restauration : {backup_avant_restore}")
        print(f"📄 Fichier de confirmation : RESTAURATION_ETAT6_CONFIRMEE.txt")
        print(f"📅 Date : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        
        print(f"\n🚀 Pour démarrer l'application :")
        print(f"   python manage.py runserver")
        
        print(f"\n📋 Fonctionnalités disponibles :")
        print(f"   - Gestion complète des retraits")
        print(f"   - Interface moderne avec filtres")
        print(f"   - Statistiques en temps réel")
        print(f"   - Validation des formulaires")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR lors de la restauration : {str(e)}")
        print(f"🔧 Veuillez vérifier que la sauvegarde {nom_etat} existe.")
        return False

if __name__ == "__main__":
    print("🔄 Démarrage du script de restauration...")
    success = restore_etat6()
    
    if success:
        print("\n✅ Restauration de l'état 6 terminée avec succès !")
        print("📋 L'application est maintenant restaurée avec tous les templates de retraits.")
    else:
        print("\n❌ Échec de la restauration.")
        print("🔧 Veuillez vérifier que la sauvegarde existe et que vous avez les permissions nécessaires.") 