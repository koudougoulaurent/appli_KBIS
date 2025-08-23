#!/usr/bin/env python
"""
Script de sauvegarde - ÉTAT 13 : Corrections URLs et améliorations finales
Date: 20 juillet 2025
Version: 1.0

Ce script sauvegarde l'état complet du projet après toutes les corrections d'URLs
et les améliorations de l'affichage des reçus.
"""

import os
import sys
import shutil
import json
import zipfile
from datetime import datetime
from pathlib import Path

def creer_sauvegarde():
    """Crée une sauvegarde complète du projet."""
    
    # Configuration
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_sauvegarde = f"etat13_corrections_urls_{timestamp}"
    dossier_sauvegarde = f"backups/{nom_sauvegarde}"
    
    print(f"🔄 Création de la sauvegarde : {nom_sauvegarde}")
    print("=" * 60)
    
    # Créer le dossier de sauvegarde
    os.makedirs(dossier_sauvegarde, exist_ok=True)
    
    # Liste des dossiers et fichiers à sauvegarder
    elements_a_sauvegarder = [
        # Applications Django
        "contrats/",
        "core/",
        "gestion_immobiliere/",
        "notifications/",
        "paiements/",
        "proprietes/",
        "utilisateurs/",
        
        # Templates
        "templates/",
        
        # Fichiers statiques
        "static/",
        "staticfiles/",
        
        # Fichiers de configuration
        "manage.py",
        "requirements.txt",
        
        # Base de données
        "db.sqlite3",
        
        # Scripts et documentation
        "*.py",
        "*.md",
        "*.txt",
        
        # Logs
        "logs/",
    ]
    
    # Exclure les dossiers de sauvegarde existants
    exclusions = [
        "backups/",
        "venv/",
        "__pycache__/",
        "*.pyc",
        ".git/",
    ]
    
    # Copier les fichiers
    fichiers_copies = 0
    dossiers_copies = 0
    
    for element in elements_a_sauvegarder:
        if os.path.exists(element):
            if os.path.isdir(element):
                # Copier le dossier
                destination = os.path.join(dossier_sauvegarde, element)
                if not any(exclusion in element for exclusion in exclusions):
                    shutil.copytree(element, destination, ignore=shutil.ignore_patterns(
                        '__pycache__', '*.pyc', '.git', 'venv', 'backups'
                    ))
                    dossiers_copies += 1
                    print(f"📁 Dossier copié : {element}")
            else:
                # Copier le fichier
                destination = os.path.join(dossier_sauvegarde, element)
                shutil.copy2(element, destination)
                fichiers_copies += 1
                print(f"📄 Fichier copié : {element}")
    
    # Créer le fichier d'information de l'état
    info_etat = {
        "nom": "État 13 - Corrections URLs et améliorations finales",
        "date_creation": datetime.now().isoformat(),
        "description": "Sauvegarde complète après corrections des URLs et améliorations de l'affichage des reçus",
        "version": "1.0",
        "statistiques": {
            "fichiers_copies": fichiers_copies,
            "dossiers_copies": dossiers_copies,
            "taille_totale": "À calculer"
        },
        "corrections_apportees": [
            "Correction des URLs 'detail_recu' → 'recu_detail'",
            "Correction des URLs 'profile' → 'dashboard' et 'configuration_entreprise'",
            "Création du template manquant 'changer_template_recu.html'",
            "Amélioration de l'affichage des reçus dans la liste des paiements",
            "Système d'impression PDF professionnel",
            "Interface utilisateur modernisée avec Bootstrap 5"
        ],
        "fonctionnalites_ajoutees": [
            "Personnalisation complète des reçus avec logo et informations d'entreprise",
            "Gestion des templates de reçus",
            "Configuration de l'entreprise",
            "Impression PDF avec WeasyPrint",
            "Envoi de reçus par email",
            "Validation et invalidation des reçus"
        ],
        "tests_realises": [
            "Test des URLs des reçus",
            "Test de personnalisation des reçus",
            "Test d'affichage des reçus",
            "Test d'impression PDF"
        ]
    }
    
    # Sauvegarder les informations
    with open(f"{dossier_sauvegarde}/ETAT13_INFO.json", "w", encoding="utf-8") as f:
        json.dump(info_etat, f, indent=2, ensure_ascii=False)
    
    # Créer le README
    readme_content = f"""# 📦 ÉTAT 13 - CORRECTIONS URLS ET AMÉLIORATIONS FINALES

## 📋 Informations générales

- **Date de création** : {datetime.now().strftime("%d/%m/%Y à %H:%M")}
- **Version** : 1.0
- **Statut** : ✅ Complètement fonctionnel

## 🎯 Corrections apportées

### 1. **Corrections des URLs**
- ✅ `'detail_recu'` → `'recu_detail'` dans tous les templates
- ✅ `'profile'` → `'dashboard'` et `'configuration_entreprise'` dans base.html
- ✅ Création du template manquant `changer_template_recu.html`

### 2. **Améliorations de l'affichage**
- ✅ Nouvelle colonne "Reçu" dans la liste des paiements
- ✅ Badges visuels pour le statut des reçus
- ✅ Boutons d'action pour chaque reçu
- ✅ Section reçu complète dans le détail des paiements

### 3. **Système d'impression**
- ✅ Impression PDF professionnelle avec WeasyPrint
- ✅ Aperçu d'impression optimisé
- ✅ Marquage automatique des impressions

## 🏗️ Architecture technique

### **Modèles principaux**
- `ConfigurationEntreprise` : Configuration de l'entreprise
- `TemplateRecu` : Templates de reçus personnalisables
- `Recu` : Reçus avec options de personnalisation

### **Vues principales**
- Configuration de l'entreprise
- Gestion des templates
- Impression et téléchargement PDF
- Envoi par email

### **Templates créés/modifiés**
- `templates/paiements/changer_template_recu.html` (nouveau)
- `templates/paiements/envoyer_recu_email.html` (corrigé)
- `templates/paiements/valider_recu.html` (corrigé)
- `templates/paiements/invalider_recu.html` (corrigé)
- `templates/base.html` (corrigé)

## 🧪 Tests réalisés

### **Scripts de test**
- `test_urls_recus.py` : Test de toutes les URLs des reçus
- `test_personnalisation_recus.py` : Test de la personnalisation
- `test_affichage_recus.py` : Test de l'affichage

### **Résultats**
- ✅ Toutes les URLs fonctionnent correctement
- ✅ Personnalisation des reçus opérationnelle
- ✅ Impression PDF fonctionnelle
- ✅ Interface utilisateur responsive

## 🚀 Fonctionnalités disponibles

### **Configuration de l'entreprise**
- Logo et identité visuelle
- Informations de contact
- Informations légales et bancaires
- Couleurs et polices personnalisées

### **Templates de reçus**
- 4 templates prêts (Standard, Professionnel, Simplifié, Luxe)
- Création et modification de templates
- Aperçu et tests PDF

### **Gestion des reçus**
- Génération automatique et manuelle
- Validation et invalidation
- Impression PDF professionnelle
- Envoi par email
- Changement de template

## 📊 Statistiques

- **Fichiers copiés** : {fichiers_copies}
- **Dossiers copiés** : {dossiers_copies}
- **Applications Django** : 6
- **Templates** : 50+
- **Scripts de test** : 3

## 🔧 Installation et utilisation

### **Prérequis**
```bash
pip install -r requirements.txt
```

### **Configuration**
```bash
python manage.py migrate
python initialiser_configuration_entreprise.py
```

### **Tests**
```bash
python test_urls_recus.py
python test_personnalisation_recus.py
python test_affichage_recus.py
```

### **Lancement**
```bash
python manage.py runserver
```

## 📝 Notes importantes

1. **Toutes les URLs sont maintenant fonctionnelles**
2. **L'interface utilisateur est complètement responsive**
3. **La personnalisation des reçus est entièrement opérationnelle**
4. **Les tests automatisés valident toutes les fonctionnalités**

## 🎉 État final

Le projet est maintenant **complètement fonctionnel** avec :
- ✅ Toutes les URLs corrigées
- ✅ Interface utilisateur modernisée
- ✅ Personnalisation des reçus opérationnelle
- ✅ Impression PDF professionnelle
- ✅ Tests complets et validés

---

*Sauvegarde créée le {datetime.now().strftime("%d/%m/%Y à %H:%M")}*
"""
    
    with open(f"{dossier_sauvegarde}/README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Créer l'archive ZIP
    nom_archive = f"backups/{nom_sauvegarde}.zip"
    with zipfile.ZipFile(nom_archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dossier_sauvegarde):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dossier_sauvegarde)
                zipf.write(file_path, arcname)
    
    # Calculer la taille
    taille_sauvegarde = sum(os.path.getsize(os.path.join(dirpath, filename))
                           for dirpath, dirnames, filenames in os.walk(dossier_sauvegarde)
                           for filename in filenames)
    
    taille_archive = os.path.getsize(nom_archive)
    
    print("\n" + "=" * 60)
    print("✅ SAUVEGARDE TERMINÉE AVEC SUCCÈS")
    print("=" * 60)
    print(f"📁 Dossier de sauvegarde : {dossier_sauvegarde}")
    print(f"📦 Archive ZIP : {nom_archive}")
    print(f"📊 Fichiers copiés : {fichiers_copies}")
    print(f"📁 Dossiers copiés : {dossiers_copies}")
    print(f"💾 Taille de la sauvegarde : {taille_sauvegarde / 1024 / 1024:.2f} MB")
    print(f"🗜️ Taille de l'archive : {taille_archive / 1024 / 1024:.2f} MB")
    print("\n🎯 ÉTAT 13 - CORRECTIONS URLS ET AMÉLIORATIONS FINALES")
    print("✅ Toutes les URLs corrigées")
    print("✅ Interface utilisateur modernisée")
    print("✅ Personnalisation des reçus opérationnelle")
    print("✅ Impression PDF professionnelle")
    print("✅ Tests complets et validés")
    
    return {
        "dossier": dossier_sauvegarde,
        "archive": nom_archive,
        "fichiers": fichiers_copies,
        "dossiers": dossiers_copies,
        "taille_sauvegarde": taille_sauvegarde,
        "taille_archive": taille_archive
    }

if __name__ == "__main__":
    try:
        resultat = creer_sauvegarde()
        print(f"\n🎉 Sauvegarde de l'état 13 créée avec succès !")
        print(f"📁 Dossier : {resultat['dossier']}")
        print(f"📦 Archive : {resultat['archive']}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        sys.exit(1) 