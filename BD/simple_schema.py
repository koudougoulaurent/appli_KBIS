#!/usr/bin/env python
"""
Générateur de schéma simple pour KBIS INTERNATIONAL
Génère automatiquement la documentation de la base de données
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')

try:
    django.setup()
except Exception as e:
    print(f"⚠️ Erreur lors de l'initialisation de Django: {e}")
    print("💡 Assurez-vous que le projet Django est correctement configuré")
    sys.exit(1)

from django.apps import apps
import json
from datetime import datetime


def generate_simple_schema():
    """Générer le schéma de base de données"""
    print("🚀 GÉNÉRATION DU SCHÉMA KBIS INTERNATIONAL")
    print("=" * 50)
    
    try:
        # Analyser les modèles
        models_data = {}
        relationships = []
        apps_analyzed = 0
        models_analyzed = 0
        
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('django.') or app_config.name in ['admin', 'auth', 'contenttypes', 'sessions']:
                continue
                
            app_name = app_config.name
            print(f"📱 Application: {app_name}")
            apps_analyzed += 1
            
            try:
                for model in app_config.get_models():
                    model_name = model.__name__
                    print(f"  📋 Modèle: {model_name}")
                    models_analyzed += 1
                    
                    # Analyser les champs
                    fields = []
                    for field in model._meta.get_fields():
                        if hasattr(field, 'name'):
                            field_info = {
                                'name': field.name,
                                'type': field.__class__.__name__,
                                'verbose_name': getattr(field, 'verbose_name', field.name),
                                'null': getattr(field, 'null', False),
                                'blank': getattr(field, 'blank', False),
                                'unique': getattr(field, 'unique', False),
                                'primary_key': getattr(field, 'primary_key', False),
                            }
                            fields.append(field_info)
                            
                            # Analyser les relations
                            if hasattr(field, 'related_model') and field.related_model:
                                rel_info = {
                                    'from_model': f"{model._meta.app_label}.{model_name}",
                                    'to_model': f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
                                    'field_name': field.name,
                                    'relation_type': field.__class__.__name__,
                                }
                                relationships.append(rel_info)
                    
                    models_data[f"{app_name}.{model_name}"] = {
                        'name': model_name,
                        'app': app_name,
                        'verbose_name': model._meta.verbose_name,
                        'fields': fields,
                    }
            except Exception as e:
                print(f"  ⚠️ Erreur lors de l'analyse du modèle {model_name}: {e}")
                continue
        
        # Sauvegarder les fichiers
        save_documentation(models_data, relationships)
        
        print(f"\n🎉 GÉNÉRATION TERMINÉE !")
        print(f"📊 Statistiques:")
        print(f"   - Applications analysées: {apps_analyzed}")
        print(f"   - Modèles analysés: {models_analyzed}")
        print(f"   - Relations trouvées: {len(relationships)}")
        print("📁 Fichiers créés dans BD/:")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        print("💡 Vérifiez la configuration Django et réessayez")
        sys.exit(1)


def save_documentation(models_data, relationships):
    """Sauvegarder la documentation"""
    
    # Documentation complète
    with open('BD/documentation_complete.md', 'w', encoding='utf-8') as f:
        f.write("# DOCUMENTATION COMPLÈTE - KBIS INTERNATIONAL\n\n")
        f.write(f"*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*\n\n")
        
        f.write("## 📋 Vue d'ensemble\n\n")
        f.write(f"**Nombre de modèles:** {len(models_data)}\n")
        f.write(f"**Nombre de relations:** {len(relationships)}\n\n")
        
        # Par application
        apps_data = {}
        for model_key, model_info in models_data.items():
            app_name = model_info['app']
            if app_name not in apps_data:
                apps_data[app_name] = []
            apps_data[app_name].append(model_info)
        
        for app_name, models_list in apps_data.items():
            f.write(f"## 📱 {app_name.upper()}\n\n")
            
            for model_info in models_list:
                f.write(f"### {model_info['verbose_name']} (`{model_info['name']}`)\n\n")
                
                f.write("#### Champs\n")
                f.write("| Nom | Type | Description | Null | Unique | PK |\n")
                f.write("|-----|------|-------------|------|--------|----|\n")
                
                for field in model_info['fields']:
                    null_str = "✅" if field['null'] else "❌"
                    unique_str = "✅" if field['unique'] else "❌"
                    pk_str = "✅" if field['primary_key'] else "❌"
                    f.write(f"| `{field['name']}` | {field['type']} | {field['verbose_name']} | {null_str} | {unique_str} | {pk_str} |\n")
                
                f.write("\n---\n\n")
    
    # Diagramme de classes simple
    with open('BD/diagramme_classes_simple.md', 'w', encoding='utf-8') as f:
        f.write("# DIAGRAMME DE CLASSES - KBIS INTERNATIONAL\n\n")
        f.write("## Structure des modèles\n\n")
        
        for app_name, models_list in apps_data.items():
            f.write(f"### {app_name.upper()}\n\n")
            
            for model_info in models_list:
                f.write(f"#### {model_info['name']}\n")
                f.write(f"**Description:** {model_info['verbose_name']}\n\n")
                
                f.write("**Champs principaux:**\n")
                for field in model_info['fields'][:10]:
                    f.write(f"- `{field['name']}` ({field['type']}) - {field['verbose_name']}\n")
                
                if len(model_info['fields']) > 10:
                    f.write(f"- ... et {len(model_info['fields']) - 10} autres champs\n")
                
                f.write("\n")
    
    # Diagramme de cas d'utilisation
    with open('BD/diagramme_cas_utilisation.md', 'w', encoding='utf-8') as f:
        f.write("# DIAGRAMME DE CAS D'UTILISATION - KBIS INTERNATIONAL\n\n")
        f.write("## Acteurs\n\n")
        f.write("- **👑 Administrateur:** Gestion complète du système\n")
        f.write("- **💰 Caissier:** Gestion des paiements et reçus\n")
        f.write("- **🔍 Contrôleur:** Gestion des propriétés et contrats\n")
        f.write("- **⭐ Utilisateur Privilégié:** Accès étendu\n\n")
        
        f.write("## Modules et fonctionnalités\n\n")
        f.write("### 👥 Gestion des Utilisateurs\n")
        f.write("- Créer utilisateur\n")
        f.write("- Modifier utilisateur\n")
        f.write("- Supprimer utilisateur\n")
        f.write("- Gérer groupes de travail\n")
        f.write("- Assigner permissions\n\n")
        
        f.write("### 🏢 Gestion Immobilière\n")
        f.write("- Créer propriété\n")
        f.write("- Modifier propriété\n")
        f.write("- Supprimer propriété\n")
        f.write("- Gérer bailleurs\n")
        f.write("- Gérer locataires\n")
        f.write("- Gérer unités locatives\n\n")
        
        f.write("### 📄 Gestion des Contrats\n")
        f.write("- Créer contrat\n")
        f.write("- Modifier contrat\n")
        f.write("- Résilier contrat\n")
        f.write("- Gérer quittances\n")
        f.write("- Gérer états des lieux\n\n")
        
        f.write("### 💰 Gestion des Paiements\n")
        f.write("- Enregistrer paiement\n")
        f.write("- Générer reçu\n")
        f.write("- Gérer retraits\n")
        f.write("- Paiements partiels\n")
        f.write("- Rapports financiers\n\n")
        
        f.write("### 🔒 Sécurité\n")
        f.write("- Surveiller sécurité\n")
        f.write("- Gérer alertes\n")
        f.write("- Audit des actions\n\n")
    
    # Guide de migration
    with open('BD/guide_migration.md', 'w', encoding='utf-8') as f:
        f.write("# GUIDE DE MIGRATION - KBIS INTERNATIONAL\n\n")
        f.write("## 🚀 Commandes essentielles\n\n")
        f.write("```bash\n")
        f.write("# Créer une migration\n")
        f.write("python manage.py makemigrations\n\n")
        f.write("# Appliquer les migrations\n")
        f.write("python manage.py migrate\n\n")
        f.write("# Voir l'état des migrations\n")
        f.write("python manage.py showmigrations\n\n")
        f.write("# Créer une migration pour une app spécifique\n")
        f.write("python manage.py makemigrations <app_name>\n\n")
        f.write("# Appliquer une migration spécifique\n")
        f.write("python manage.py migrate <app_name> <migration_number>\n")
        f.write("```\n\n")
        
        f.write("## 📋 Checklist avant migration\n\n")
        f.write("- [ ] Sauvegarder la base de données\n")
        f.write("- [ ] Tester en environnement de développement\n")
        f.write("- [ ] Vérifier les contraintes de clés étrangères\n")
        f.write("- [ ] Documenter les changements\n")
        f.write("- [ ] Informer l'équipe\n\n")
        
        f.write("## ⚠️ Points d'attention\n\n")
        f.write("### Modèles avec suppression logique\n")
        f.write("- `Utilisateur` (is_deleted)\n")
        f.write("- `Propriete` (is_deleted)\n")
        f.write("- `Bailleur` (is_deleted)\n")
        f.write("- `Locataire` (is_deleted)\n\n")
        
        f.write("### Relations critiques\n")
        f.write("- `Contrat` → `Propriete` (PROTECT)\n")
        f.write("- `Contrat` → `Locataire` (PROTECT)\n")
        f.write("- `Paiement` → `Contrat` (PROTECT)\n\n")
        
        f.write("### Modèles principaux par application\n")
        f.write("- **utilisateurs:** Utilisateur, GroupeTravail\n")
        f.write("- **proprietes:** Propriete, Bailleur, Locataire, TypeBien\n")
        f.write("- **contrats:** Contrat, Quittance, EtatLieux\n")
        f.write("- **paiements:** Paiement, Recu, Retrait, CompteBancaire\n")
        f.write("- **core:** NiveauAcces, AuditLog\n")
        f.write("- **notifications:** Notification\n\n")
    
    # Schéma JSON
    schema_data = {
        'generated_at': datetime.now().isoformat(),
        'models': models_data,
        'relationships': relationships
    }
    
    with open('BD/schema_complet.json', 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, indent=2, ensure_ascii=False)
    
    # Résumé des fichiers
    print("✅ Fichiers générés:")
    print("   - documentation_complete.md")
    print("   - diagramme_classes_simple.md")
    print("   - diagramme_cas_utilisation.md")
    print("   - guide_migration.md")
    print("   - schema_complet.json")


if __name__ == "__main__":
    generate_simple_schema()
