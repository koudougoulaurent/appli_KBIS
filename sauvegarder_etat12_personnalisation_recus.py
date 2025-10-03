#!/usr/bin/env python
"""
Script pour sauvegarder l'état final du projet avec la personnalisation des reçus
"""

import os
import sys
import shutil
import json
import zipfile
from datetime import datetime
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise, TemplateRecu
from paiements.models import Paiement, Recu
from proprietes.models import Propriete, Locataire, Bailleur
from contrats.models import Contrat
from utilisateurs.models import Utilisateur

def sauvegarder_etat12():
    """Sauvegarde l'état final avec la personnalisation des reçus."""
    
    print("🎨 SAUVEGARDE ÉTAT 12 - PERSONNALISATION DES REÇUS")
    print("=" * 80)
    
    # Créer le répertoire de sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/etat12_personnalisation_recus_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"📁 Création du répertoire de sauvegarde : {backup_dir}")
    
    # Copier la base de données
    if os.path.exists('db.sqlite3'):
        shutil.copy2('db.sqlite3', os.path.join(backup_dir, 'db.sqlite3'))
        print("✅ Base de données copiée")
    
    # Copier les fichiers de configuration
    config_files = [
        'manage.py',
        'requirements.txt',
        'README.md',
        'gestion_immobiliere/settings.py',
        'gestion_immobiliere/urls.py',
    ]
    
    for file_path in config_files:
        if os.path.exists(file_path):
            dest_path = os.path.join(backup_dir, file_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)
            print(f"✅ {file_path} copié")
    
    # Copier les applications
    apps = ['core', 'paiements', 'proprietes', 'contrats', 'utilisateurs', 'notifications']
    
    for app in apps:
        if os.path.exists(app):
            dest_path = os.path.join(backup_dir, app)
            shutil.copytree(app, dest_path, dirs_exist_ok=True)
            print(f"✅ Application {app} copiée")
    
    # Copier les templates
    if os.path.exists('templates'):
        dest_path = os.path.join(backup_dir, 'templates')
        shutil.copytree('templates', dest_path, dirs_exist_ok=True)
        print("✅ Templates copiés")
    
    # Copier les fichiers statiques
    if os.path.exists('static'):
        dest_path = os.path.join(backup_dir, 'static')
        shutil.copytree('static', dest_path, dirs_exist_ok=True)
        print("✅ Fichiers statiques copiés")
    
    if os.path.exists('staticfiles'):
        dest_path = os.path.join(backup_dir, 'staticfiles')
        shutil.copytree('staticfiles', dest_path, dirs_exist_ok=True)
        print("✅ Fichiers staticfiles copiés")
    
    # Copier les médias (logos, etc.)
    if os.path.exists('media'):
        dest_path = os.path.join(backup_dir, 'media')
        shutil.copytree('media', dest_path, dirs_exist_ok=True)
        print("✅ Fichiers médias copiés")
    
    # Collecter les statistiques
    print("\n📊 Collecte des statistiques...")
    
    stats = {
        'timestamp': timestamp,
        'etat': 'etat12_personnalisation_recus',
        'description': 'État final avec personnalisation complète des reçus',
        
        # Statistiques générales
        'paiements': {
            'total': Paiement.objects.count(),
            'valides': Paiement.objects.filter(statut='valide').count(),
            'en_attente': Paiement.objects.filter(statut='en_attente').count(),
            'refuses': Paiement.objects.filter(statut='refuse').count(),
        },
        
        'recus': {
            'total': Recu.objects.count(),
            'valides': Recu.objects.filter(valide=True).count(),
            'imprimes': Recu.objects.filter(imprime=True).count(),
            'envoyes_email': Recu.objects.filter(envoye_email=True).count(),
        },
        
        'proprietes': {
            'total': Propriete.objects.count(),
            'louees': Propriete.objects.filter(disponible=False).count(),
            'disponibles': Propriete.objects.filter(disponible=True).count(),
        },
        
        'utilisateurs': {
            'total': Utilisateur.objects.count(),
            'actifs': Utilisateur.objects.filter(is_active=True).count(),
        },
        
        'contrats': {
            'total': Contrat.objects.count(),
            'actifs': Contrat.objects.filter(est_actif=True).count(),
        },
        
        'locataires': {
            'total': Locataire.objects.count(),
            'actifs': Locataire.objects.filter(est_actif=True).count(),
        },
        
        'bailleurs': {
            'total': Bailleur.objects.count(),
            'actifs': Bailleur.objects.filter(est_actif=True).count(),
        },
        
        # Configuration entreprise
        'configuration_entreprise': {
            'existe': ConfigurationEntreprise.objects.filter(active=True).exists(),
            'nom': ConfigurationEntreprise.get_configuration_active().nom_entreprise if ConfigurationEntreprise.objects.filter(active=True).exists() else None,
            'logo': ConfigurationEntreprise.get_configuration_active().logo.name if ConfigurationEntreprise.objects.filter(active=True).exists() and ConfigurationEntreprise.get_configuration_active().logo else None,
        },
        
        # Templates de reçus
        'templates_recus': {
            'total': TemplateRecu.objects.count(),
            'actifs': TemplateRecu.objects.filter(actif=True).count(),
            'par_defaut': TemplateRecu.objects.filter(par_defaut=True).count(),
            'listes': list(TemplateRecu.objects.values_list('nom', flat=True)),
        },
        
        # Fonctionnalités implémentées
        'fonctionnalites': [
            'Configuration complète de l\'entreprise',
            'Gestion des logos et informations de contact',
            'Personnalisation des couleurs et polices',
            'Gestion des informations légales (SIRET, TVA, RCS)',
            'Gestion des informations bancaires (IBAN, BIC)',
            'Templates de reçus personnalisables',
            'Génération PDF avec ReportLab personnalisé',
            'Interface de configuration intuitive',
            'Gestion des templates avec aperçu',
            'Validation des données et sécurité',
            'API de configuration',
            'Tests complets de personnalisation',
        ],
        
        # Fichiers générés
        'fichiers_generes': [
            'core/models.py - Modèles ConfigurationEntreprise et TemplateRecu',
            'core/views.py - Vues de configuration et gestion des templates',
            'core/urls.py - URLs pour la configuration',
            'templates/core/configuration_entreprise.html - Interface de configuration',
            'templates/core/gestion_templates.html - Interface de gestion des templates',
            'paiements/views.py - Fonction PDF personnalisée',
            'initialiser_configuration_entreprise.py - Script d\'initialisation',
            'test_personnalisation_recus.py - Script de test complet',
            'PERSONNALISATION_RECUS_ENTREPRISE.md - Documentation complète',
        ],
    }
    
    # Sauvegarder les statistiques
    stats_file = os.path.join(backup_dir, 'etat12_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print("✅ Statistiques sauvegardées")
    
    # Créer le fichier README
    readme_content = f"""# 🎨 ÉTAT 12 - PERSONNALISATION DES REÇUS

## 📋 Description

Cette sauvegarde représente l'état final du projet avec le système complet de personnalisation des reçus implémenté.

## 🗓️ Date de sauvegarde

**{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}**

## 🎯 Fonctionnalités implémentées

### ✅ Configuration de l'entreprise
- Modèle `ConfigurationEntreprise` complet
- Gestion du logo et informations de contact
- Personnalisation des couleurs et polices
- Informations légales (SIRET, TVA, RCS)
- Informations bancaires (IBAN, BIC)
- Options d'affichage configurables
- Textes personnalisés (pied de page, conditions)

### ✅ Templates de reçus
- Modèle `TemplateRecu` pour les modèles personnalisés
- 4 templates par défaut créés (Standard, Professionnel, Simplifié, Luxe)
- Gestion des couleurs et polices par template
- Options d'affichage par template
- Interface de gestion complète

### ✅ Génération PDF personnalisée
- Fonction `generer_pdf_reportlab()` refactorisée
- Utilisation de la configuration de l'entreprise
- Logo et informations personnalisées
- Couleurs et polices configurables
- Informations légales conditionnelles
- Mapping automatique des polices ReportLab

### ✅ Interface utilisateur
- Page de configuration complète (`/core/configuration/`)
- Gestion des templates (`/core/templates/`)
- Aperçu en temps réel des modifications
- Upload et prévisualisation du logo
- Sélecteurs de couleurs et polices
- Options d'affichage configurables

### ✅ API et fonctionnalités avancées
- API de configuration (`/core/api/configuration/`)
- Validation des données (couleurs, fichiers)
- Gestion d'erreurs robuste
- Permissions administrateur
- Tests complets automatisés

## 📊 Statistiques

### Données générales
- **Paiements** : {stats['paiements']['total']} (dont {stats['paiements']['valides']} validés)
- **Reçus** : {stats['recus']['total']} (dont {stats['recus']['valides']} validés)
- **Propriétés** : {stats['proprietes']['total']} (dont {stats['proprietes']['louees']} louées)
- **Utilisateurs** : {stats['utilisateurs']['total']} (dont {stats['utilisateurs']['actifs']} actifs)
- **Contrats** : {stats['contrats']['total']} (dont {stats['contrats']['actifs']} actifs)
- **Locataires** : {stats['locataires']['total']} (dont {stats['locataires']['actifs']} actifs)
- **Bailleurs** : {stats['bailleurs']['total']} (dont {stats['bailleurs']['actifs']} actifs)

### Configuration entreprise
- **Configuration active** : {'Oui' if stats['configuration_entreprise']['existe'] else 'Non'}
- **Nom entreprise** : {stats['configuration_entreprise']['nom'] or 'Non défini'}
- **Logo** : {'Présent' if stats['configuration_entreprise']['logo'] else 'Non défini'}

### Templates de reçus
- **Total templates** : {stats['templates_recus']['total']}
- **Templates actifs** : {stats['templates_recus']['actifs']}
- **Template par défaut** : {stats['templates_recus']['par_defaut']}
- **Templates disponibles** : {', '.join(stats['templates_recus']['listes'])}

## 🚀 Installation et utilisation

### 1. Restaurer la sauvegarde
```bash
# Extraire l'archive
unzip etat12_personnalisation_recus_{timestamp}.zip

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

### 2. Initialiser la configuration
```bash
python initialiser_configuration_entreprise.py
```

### 3. Tester la personnalisation
```bash
python test_personnalisation_recus.py
```

### 4. Accéder aux interfaces
- **Configuration entreprise** : http://localhost:8000/core/configuration/
- **Gestion des templates** : http://localhost:8000/core/templates/
- **Administration** : http://localhost:8000/admin/

## 📁 Structure des fichiers

```
etat12_personnalisation_recus_{timestamp}/
├── core/                    # Application de configuration
│   ├── models.py           # Modèles ConfigurationEntreprise et TemplateRecu
│   ├── views.py            # Vues de configuration
│   ├── urls.py             # URLs de configuration
│   └── templates/          # Templates de configuration
├── paiements/              # Application des paiements
│   ├── views.py            # Fonction PDF personnalisée
│   └── models.py           # Modèles de paiements et reçus
├── templates/              # Templates HTML
│   └── core/               # Templates de configuration
├── static/                 # Fichiers statiques
├── media/                  # Fichiers médias (logos)
├── scripts/                # Scripts utilitaires
│   ├── initialiser_configuration_entreprise.py
│   └── test_personnalisation_recus.py
├── db.sqlite3              # Base de données
├── etat12_stats.json       # Statistiques détaillées
└── README.md               # Ce fichier
```

## 🎉 Résultats

Le système de personnalisation des reçus est maintenant **complètement opérationnel** et permet aux entreprises de :

- ✅ Personnaliser leur identité visuelle sur tous les reçus
- ✅ Ajouter leur logo et informations de contact
- ✅ Choisir leurs couleurs et polices préférées
- ✅ Gérer leurs informations légales et bancaires
- ✅ Créer des templates personnalisés pour différents usages
- ✅ Modifier et adapter les reçus selon leurs besoins

**🎯 Objectif atteint : Les reçus peuvent maintenant être modifiés et personnalisés avec les informations et le logo de l'entreprise !**

---

*Sauvegarde générée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*
"""
    
    readme_file = os.path.join(backup_dir, 'README.md')
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ README créé")
    
    # Créer l'archive ZIP
    zip_filename = f"backups/etat12_personnalisation_recus_{timestamp}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, backup_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Archive créée : {zip_filename}")
    
    # Nettoyer le répertoire temporaire
    shutil.rmtree(backup_dir)
    print("✅ Répertoire temporaire nettoyé")
    
    # Afficher le résumé
    print("\n" + "=" * 80)
    print("🎉 SAUVEGARDE ÉTAT 12 TERMINÉE AVEC SUCCÈS !")
    print("=" * 80)
    print(f"📁 Archive : {zip_filename}")
    print(f"📊 Statistiques : {stats['paiements']['total']} paiements, {stats['recus']['total']} reçus")
    print(f"🏢 Configuration : {'Active' if stats['configuration_entreprise']['existe'] else 'Non configurée'}")
    print(f"📄 Templates : {stats['templates_recus']['total']} templates créés")
    print(f"✅ Fonctionnalités : {len(stats['fonctionnalites'])} fonctionnalités implémentées")
    
    print(f"\n🚀 Le système de personnalisation des reçus est maintenant opérationnel !")
    print(f"   📋 Accédez à la configuration : /core/configuration/")
    print(f"   📄 Gérez les templates : /core/templates/")
    print(f"   🧪 Testez la personnalisation : python test_personnalisation_recus.py")

if __name__ == "__main__":
    sauvegarder_etat12() 