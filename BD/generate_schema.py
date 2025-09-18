#!/usr/bin/env python
"""
Générateur de schéma de base de données simplifié pour KBIS INTERNATIONAL
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from django.apps import apps
import json
from datetime import datetime


def generate_schema():
    """Générer le schéma de base de données"""
    print("🚀 GÉNÉRATION DU SCHÉMA KBIS INTERNATIONAL")
    print("=" * 50)
    
    # Analyser les modèles
    models_data = {}
    relationships = []
    
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('django.') or app_config.name in ['admin', 'auth', 'contenttypes', 'sessions']:
            continue
            
        app_name = app_config.name
        print(f"📱 Application: {app_name}")
        
        for model in app_config.get_models():
            model_name = model.__name__
            print(f"  📋 Modèle: {model_name}")
            
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
    
    # Générer le diagramme de classes Mermaid
    print("📊 Génération du diagramme de classes...")
    mermaid_class = generate_class_diagram(models_data, relationships)
    
    # Générer le diagramme de cas d'utilisation
    print("👥 Génération du diagramme de cas d'utilisation...")
    mermaid_use_case = generate_use_case_diagram()
    
    # Sauvegarder les fichiers
    save_files(mermaid_class, mermaid_use_case, models_data, relationships)
    
    print("\n🎉 GÉNÉRATION TERMINÉE !")
    print("📁 Fichiers créés dans BD/:")


def generate_class_diagram(models_data, relationships):
    """Générer le diagramme de classes Mermaid"""
    lines = ["classDiagram"]
    
    # Ajouter les classes
    for model_key, model_info in models_data.items():
        class_name = model_info['name']
        lines.append(f"    class {class_name} {{")
        
        # Ajouter les champs principaux
        for field in model_info['fields'][:8]:
            field_name = field['name']
            field_type = field['type'].replace('Field', '').replace('Char', 'String')
            
            if field['primary_key']:
                field_name = f"🔑 {field_name}"
            elif field['unique']:
                field_name = f"🔒 {field_name}"
            
            lines.append(f"        +{field_name}: {field_type}")
        
        if len(model_info['fields']) > 8:
            lines.append(f"        +... {len(model_info['fields']) - 8} autres")
        
        lines.append("    }")
        lines.append("")
    
    # Ajouter les relations principales
    for rel in relationships[:20]:  # Limiter pour la lisibilité
        from_class = rel['from_model'].split('.')[-1]
        to_class = rel['to_model'].split('.')[-1]
        
        if rel['relation_type'] == 'ForeignKey':
            lines.append(f"    {from_class} ||--o{ {to_class} : {rel['field_name']}")
        elif rel['relation_type'] == 'OneToOneField':
            lines.append(f"    {from_class} ||--|| {to_class} : {rel['field_name']}")
        elif rel['relation_type'] == 'ManyToManyField':
            lines.append(f"    {from_class} ||--o{{ {to_class} : {rel['field_name']}")
    
    return "\n".join(lines)


def generate_use_case_diagram():
    """Générer le diagramme de cas d'utilisation"""
    lines = ["graph TD"]
    
    # Acteurs
    lines.append("    Admin[👑 Administrateur]")
    lines.append("    Caisse[💰 Caissier]")
    lines.append("    Controle[🔍 Contrôleur]")
    lines.append("    Privilege[⭐ Utilisateur Privilégié]")
    lines.append("")
    
    # Modules principaux
    modules = {
        "Utilisateurs": ["Créer utilisateur", "Modifier utilisateur", "Gérer groupes"],
        "Immobilier": ["Créer propriété", "Gérer bailleurs", "Gérer locataires"],
        "Contrats": ["Créer contrat", "Gérer quittances", "États des lieux"],
        "Paiements": ["Enregistrer paiement", "Générer reçu", "Paiements partiels"],
        "Sécurité": ["Surveiller sécurité", "Gérer alertes", "Audit"]
    }
    
    for module, cases in modules.items():
        lines.append(f"    subgraph {module}")
        for case in cases:
            case_id = case.replace(" ", "_").replace("é", "e")
            lines.append(f"        {case_id}[\"{case}\"]")
        lines.append("    end")
        lines.append("")
    
    # Relations principales
    relations = [
        ("Admin", "Créer utilisateur"), ("Admin", "Modifier utilisateur"),
        ("Caisse", "Enregistrer paiement"), ("Caisse", "Générer reçu"),
        ("Controle", "Créer propriété"), ("Controle", "Créer contrat"),
        ("Privilege", "Créer utilisateur"), ("Privilege", "Surveiller sécurité")
    ]
    
    for actor, case in relations:
        case_id = case.replace(" ", "_").replace("é", "e")
        lines.append(f"    {actor} --> {case_id}")
    
    return "\n".join(lines)


def save_files(mermaid_class, mermaid_use_case, models_data, relationships):
    """Sauvegarder tous les fichiers"""
    
    # Diagramme de classes
    with open('BD/diagramme_classes.md', 'w', encoding='utf-8') as f:
        f.write("# DIAGRAMME DE CLASSES - KBIS INTERNATIONAL\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_class)
        f.write("\n```\n")
    
    # Diagramme de cas d'utilisation
    with open('BD/diagramme_cas_utilisation.md', 'w', encoding='utf-8') as f:
        f.write("# DIAGRAMME DE CAS D'UTILISATION - KBIS INTERNATIONAL\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_use_case)
        f.write("\n```\n")
    
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
                
                f.write("#### Champs principaux\n")
                f.write("| Nom | Type | Description |\n")
                f.write("|-----|------|-------------|\n")
                
                for field in model_info['fields'][:10]:
                    f.write(f"| `{field['name']}` | {field['type']} | {field['verbose_name']} |\n")
                
                f.write("\n---\n\n")
    
    # Schéma JSON
    schema_data = {
        'generated_at': datetime.now().isoformat(),
        'models': models_data,
        'relationships': relationships
    }
    
    with open('BD/schema_complet.json', 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, indent=2, ensure_ascii=False)
    
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
        f.write("python manage.py showmigrations\n")
        f.write("```\n\n")
        f.write("## ⚠️ Points d'attention\n\n")
        f.write("- Modèles avec suppression logique: Utilisateur, Propriete, Bailleur, Locataire\n")
        f.write("- Relations critiques: Contrat → Propriete (PROTECT)\n")
        f.write("- Toujours sauvegarder avant migration\n")


if __name__ == "__main__":
    generate_schema()
