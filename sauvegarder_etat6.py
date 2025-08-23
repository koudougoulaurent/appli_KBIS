#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de sauvegarde pour l'état 6 de l'application de gestion immobilière
Sauvegarde complète du projet avec tous les templates de retraits créés
"""

import os
import shutil
import zipfile
from datetime import datetime
import json

def sauvegarder_etat6():
    """Sauvegarde l'état actuel de l'application sous le nom 'etat6'"""
    
    # Configuration
    nom_etat = "etat6"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_dossier = f"{nom_etat}_{timestamp}"
    chemin_sauvegarde = os.path.join("backups", nom_dossier)
    
    # Dossiers et fichiers à sauvegarder
    dossiers_a_sauvegarder = [
        "core",
        "utilisateurs", 
        "proprietes",
        "contrats",
        "paiements",
        "notifications",
        "templates",
        "static",
        "media",
        "logs"
    ]
    
    fichiers_a_sauvegarder = [
        "manage.py",
        "db.sqlite3",
        "requirements.txt",
        "README.md",
        "ETAT5_SYNTHESE_FINALE.md",
        "ETAT4_SYNTHESE_FINALE.md",
        "ETAT2_INFO.md",
        "CORRECTION_ERREURS_COMPLETE.md",
        "CORRECTION_NOTIFICATIONS.md",
        "API_DOCUMENTATION.md",
        "AMELIORATION_PAGES_WEB.md",
        "SECURITE_FORMULAIRES_COMPLETE.md"
    ]
    
    try:
        print(f"🚀 Début de la sauvegarde de l'état {nom_etat}...")
        
        # Créer le dossier de sauvegarde
        os.makedirs(chemin_sauvegarde, exist_ok=True)
        print(f"✅ Dossier de sauvegarde créé : {chemin_sauvegarde}")
        
        # Sauvegarder les dossiers
        for dossier in dossiers_a_sauvegarder:
            if os.path.exists(dossier):
                chemin_source = dossier
                chemin_destination = os.path.join(chemin_sauvegarde, dossier)
                
                if os.path.isdir(chemin_source):
                    shutil.copytree(chemin_source, chemin_destination, dirs_exist_ok=True)
                    print(f"✅ Dossier sauvegardé : {dossier}")
                else:
                    shutil.copy2(chemin_source, chemin_destination)
                    print(f"✅ Fichier sauvegardé : {dossier}")
            else:
                print(f"⚠️  Dossier/Fichier non trouvé : {dossier}")
        
        # Sauvegarder les fichiers individuels
        for fichier in fichiers_a_sauvegarder:
            if os.path.exists(fichier):
                chemin_source = fichier
                chemin_destination = os.path.join(chemin_sauvegarde, fichier)
                shutil.copy2(chemin_source, chemin_destination)
                print(f"✅ Fichier sauvegardé : {fichier}")
            else:
                print(f"⚠️  Fichier non trouvé : {fichier}")
        
        # Créer le fichier d'information de l'état
        info_etat = {
            "nom_etat": nom_etat,
            "timestamp_creation": timestamp,
            "description": "État 6 - Gestion complète des retraits avec tous les templates créés",
            "fonctionnalites_ajoutees": [
                "Template de liste des retraits avec filtres avancés",
                "Template de détail de retrait",
                "Template d'ajout de retrait",
                "Template de modification de retrait",
                "Vue liste_retraits améliorée avec statistiques",
                "Correction des URLs pour les retraits",
                "Interface moderne et responsive pour les retraits"
            ],
            "fichiers_principaux": [
                "templates/paiements/retraits_liste.html",
                "templates/paiements/retrait_detail.html", 
                "templates/paiements/retrait_ajouter.html",
                "templates/paiements/retrait_modifier.html",
                "paiements/views.py (vue liste_retraits améliorée)",
                "paiements/urls.py (URLs des retraits)"
            ],
            "statut": "COMPLET - Tous les templates de retraits fonctionnels",
            "serveur": "Fonctionne sans erreur",
            "urls_disponibles": [
                "/paiements/retraits/ - Liste des retraits",
                "/paiements/retraits/ajouter/ - Ajouter un retrait",
                "/paiements/retraits/detail/<id>/ - Détail d'un retrait",
                "/paiements/retraits/modifier/<id>/ - Modifier un retrait"
            ]
        }
        
        with open(os.path.join(chemin_sauvegarde, f"{nom_etat.upper()}_INFO.md"), 'w', encoding='utf-8') as f:
            f.write(f"# État {nom_etat.upper()} - Gestion Immobilière\n\n")
            f.write(f"**Date de création :** {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n\n")
            f.write(f"**Description :** {info_etat['description']}\n\n")
            
            f.write("## 🎯 Fonctionnalités Ajoutées\n\n")
            for fonctionnalite in info_etat['fonctionnalites_ajoutees']:
                f.write(f"- ✅ {fonctionnalite}\n")
            
            f.write("\n## 📁 Fichiers Principaux\n\n")
            for fichier in info_etat['fichiers_principaux']:
                f.write(f"- 📄 {fichier}\n")
            
            f.write(f"\n## 📊 Statut\n\n")
            f.write(f"- **État :** {info_etat['statut']}\n")
            f.write(f"- **Serveur :** {info_etat['serveur']}\n")
            
            f.write("\n## 🌐 URLs Disponibles\n\n")
            for url in info_etat['urls_disponibles']:
                f.write(f"- 🔗 {url}\n")
            
            f.write("\n## 🔧 Détails Techniques\n\n")
            f.write("- **Framework :** Django 4.2.7\n")
            f.write("- **Base de données :** SQLite3\n")
            f.write("- **Interface :** Bootstrap 5 + CSS personnalisé\n")
            f.write("- **Validation :** Formulaires Django avec validation JavaScript\n")
            f.write("- **Sécurité :** Authentification requise pour toutes les vues\n")
        
        # Créer un résumé JSON
        with open(os.path.join(chemin_sauvegarde, f"{nom_etat}_resume.json"), 'w', encoding='utf-8') as f:
            json.dump(info_etat, f, indent=2, ensure_ascii=False)
        
        # Créer un fichier de résumé texte
        with open(os.path.join(chemin_sauvegarde, f"resume_{nom_etat}.txt"), 'w', encoding='utf-8') as f:
            f.write(f"ÉTAT {nom_etat.upper()} - SAUVEGARDE COMPLÈTE\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Description : {info_etat['description']}\n\n")
            f.write("FONCTIONNALITÉS AJOUTÉES :\n")
            for fonctionnalite in info_etat['fonctionnalites_ajoutees']:
                f.write(f"  ✓ {fonctionnalite}\n")
            f.write(f"\nSTATUT : {info_etat['statut']}\n")
            f.write(f"SERVEUR : {info_etat['serveur']}\n")
        
        # Créer l'archive ZIP
        nom_zip = f"{nom_dossier}.zip"
        chemin_zip = os.path.join("backups", nom_zip)
        
        with zipfile.ZipFile(chemin_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(chemin_sauvegarde):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, chemin_sauvegarde)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Archive ZIP créée : {chemin_zip}")
        
        # Statistiques finales
        taille_dossier = sum(os.path.getsize(os.path.join(dirpath, filename))
                            for dirpath, dirnames, filenames in os.walk(chemin_sauvegarde)
                            for filename in filenames)
        
        print(f"\n🎉 SAUVEGARDE TERMINÉE AVEC SUCCÈS !")
        print(f"📁 Dossier : {chemin_sauvegarde}")
        print(f"📦 Archive : {chemin_zip}")
        print(f"📊 Taille : {taille_dossier / 1024 / 1024:.2f} MB")
        print(f"📅 Date : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR lors de la sauvegarde : {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Démarrage du script de sauvegarde...")
    success = sauvegarder_etat6()
    
    if success:
        print("\n✅ Sauvegarde de l'état 6 terminée avec succès !")
        print("📋 L'application est maintenant sauvegardée avec tous les templates de retraits.")
    else:
        print("\n❌ Échec de la sauvegarde.")
        print("🔧 Veuillez vérifier les permissions et l'espace disque disponible.") 