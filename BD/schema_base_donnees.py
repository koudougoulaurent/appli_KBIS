#!/usr/bin/env python
"""
Script pour générer le schéma complet de la base de données KBIS INTERNATIONAL
Génère les diagrammes de classes, cas d'utilisation et documentation
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from django.db import models
from django.apps import apps
from django.core.management import call_command
import json
from datetime import datetime


class DatabaseSchemaGenerator:
    """Générateur de schéma de base de données"""
    
    def __init__(self):
        self.models = {}
        self.relationships = []
        self.apps_info = {}
        
    def analyze_models(self):
        """Analyser tous les modèles de l'application"""
        print("🔍 Analyse des modèles de l'application...")
        
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('django.') or app_config.name in ['admin', 'auth', 'contenttypes', 'sessions']:
                continue
                
            app_name = app_config.name
            self.apps_info[app_name] = {
                'verbose_name': app_config.verbose_name,
                'models': {}
            }
            
            print(f"📱 Application: {app_name}")
            
            for model in app_config.get_models():
                model_info = self.analyze_model(model)
                self.models[f"{app_name}.{model.__name__}"] = model_info
                self.apps_info[app_name]['models'][model.__name__] = model_info
                
                print(f"  📋 Modèle: {model.__name__}")
    
    def analyze_model(self, model):
        """Analyser un modèle spécifique"""
        model_info = {
            'name': model.__name__,
            'app': model._meta.app_label,
            'verbose_name': model._meta.verbose_name,
            'verbose_name_plural': model._meta.verbose_name_plural,
            'fields': [],
            'relationships': [],
            'meta': {
                'ordering': getattr(model._meta, 'ordering', []),
                'unique_together': getattr(model._meta, 'unique_together', []),
                'index_together': getattr(model._meta, 'index_together', []),
            }
        }
        
        # Analyser les champs
        for field in model._meta.get_fields():
            if hasattr(field, 'name'):
                field_info = self.analyze_field(field)
                model_info['fields'].append(field_info)
                
                # Analyser les relations
                if hasattr(field, 'related_model') and field.related_model:
                    rel_info = self.analyze_relationship(field)
                    model_info['relationships'].append(rel_info)
                    self.relationships.append(rel_info)
        
        return model_info
    
    def analyze_field(self, field):
        """Analyser un champ spécifique"""
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'verbose_name': getattr(field, 'verbose_name', field.name),
            'help_text': getattr(field, 'help_text', ''),
            'null': getattr(field, 'null', False),
            'blank': getattr(field, 'blank', False),
            'default': str(getattr(field, 'default', None)),
            'max_length': getattr(field, 'max_length', None),
            'choices': getattr(field, 'choices', None),
            'unique': getattr(field, 'unique', False),
            'primary_key': getattr(field, 'primary_key', False),
        }
        
        # Nettoyer les valeurs par défaut
        if field_info['default'] == '<django.db.models.fields.NOT_PROVIDED>':
            field_info['default'] = None
        elif field_info['default'] == '<function now at 0x':
            field_info['default'] = 'timezone.now()'
        
        return field_info
    
    def analyze_relationship(self, field):
        """Analyser une relation"""
        rel_info = {
            'from_model': f"{field.model._meta.app_label}.{field.model.__name__}",
            'to_model': f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
            'field_name': field.name,
            'relation_type': field.__class__.__name__,
            'related_name': getattr(field, 'related_name', None),
            'on_delete': str(getattr(field, 'on_delete', None)),
            'through': getattr(field, 'through', None),
        }
        
        return rel_info
    
    def generate_mermaid_class_diagram(self):
        """Générer un diagramme de classes Mermaid"""
        print("📊 Génération du diagramme de classes...")
        
        mermaid = ["classDiagram"]
        
        # Ajouter les classes
        for model_name, model_info in self.models.items():
            class_name = model_info['name']
            app_name = model_info['app']
            
            mermaid.append(f"    class {class_name} {{")
            mermaid.append(f"        +{app_name}")
            
            # Ajouter les champs principaux
            for field in model_info['fields'][:10]:  # Limiter à 10 champs pour la lisibilité
                field_type = field['type'].replace('Field', '').replace('Char', 'String')
                field_name = field['name']
                if field['primary_key']:
                    field_name = f"🔑 {field_name}"
                elif field['unique']:
                    field_name = f"🔒 {field_name}"
                
                mermaid.append(f"        +{field_name}: {field_type}")
            
            if len(model_info['fields']) > 10:
                mermaid.append(f"        +... {len(model_info['fields']) - 10} autres champs")
            
            mermaid.append("    }")
            mermaid.append("")
        
        # Ajouter les relations
        for rel in self.relationships:
            from_class = rel['from_model'].split('.')[-1]
            to_class = rel['to_model'].split('.')[-1]
            
            if rel['relation_type'] == 'ForeignKey':
                mermaid.append(f"    {from_class} ||--o{ {to_class} : {rel['field_name']}")
            elif rel['relation_type'] == 'OneToOneField':
                mermaid.append(f"    {from_class} ||--|| {to_class} : {rel['field_name']}")
            elif rel['relation_type'] == 'ManyToManyField':
                mermaid.append(f"    {from_class} ||--o{{ {to_class} : {rel['field_name']}")
        
        return "\n".join(mermaid)
    
    def generate_use_case_diagram(self):
        """Générer un diagramme de cas d'utilisation"""
        print("👥 Génération du diagramme de cas d'utilisation...")
        
        mermaid = ["graph TD"]
        
        # Acteurs
        mermaid.append("    Admin[👑 Administrateur]")
        mermaid.append("    Caisse[💰 Caissier]")
        mermaid.append("    Controle[🔍 Contrôleur]")
        mermaid.append("    Privilege[⭐ Utilisateur Privilégié]")
        mermaid.append("")
        
        # Cas d'utilisation par module
        use_cases = {
            "Gestion des Utilisateurs": [
                "Créer utilisateur", "Modifier utilisateur", "Supprimer utilisateur",
                "Gérer groupes", "Assigner permissions"
            ],
            "Gestion Immobilière": [
                "Créer propriété", "Modifier propriété", "Supprimer propriété",
                "Gérer bailleurs", "Gérer locataires", "Gérer unités locatives"
            ],
            "Gestion des Contrats": [
                "Créer contrat", "Modifier contrat", "Résilier contrat",
                "Gérer quittances", "Gérer états des lieux"
            ],
            "Gestion des Paiements": [
                "Enregistrer paiement", "Générer reçu", "Gérer retraits",
                "Paiements partiels", "Rapports financiers"
            ],
            "Sécurité": [
                "Surveiller sécurité", "Gérer alertes", "Audit des actions"
            ]
        }
        
        # Ajouter les cas d'utilisation
        for module, cases in use_cases.items():
            mermaid.append(f"    subgraph {module}")
            for case in cases:
                case_id = case.replace(" ", "_").replace("é", "e").replace("è", "e")
                mermaid.append(f"        {case_id}[\"{case}\"]")
            mermaid.append("    end")
            mermaid.append("")
        
        # Relations acteurs-cas d'utilisation
        actor_permissions = {
            "Admin": ["Créer utilisateur", "Modifier utilisateur", "Supprimer utilisateur", "Gérer groupes", "Assigner permissions", "Surveiller sécurité", "Gérer alertes", "Audit des actions"],
            "Caisse": ["Enregistrer paiement", "Générer reçu", "Gérer retraits", "Paiements partiels", "Rapports financiers"],
            "Controle": ["Créer propriété", "Modifier propriété", "Gérer bailleurs", "Gérer locataires", "Créer contrat", "Modifier contrat", "Gérer quittances", "Gérer états des lieux"],
            "Privilege": ["Créer utilisateur", "Modifier utilisateur", "Supprimer utilisateur", "Créer propriété", "Modifier propriété", "Supprimer propriété", "Créer contrat", "Modifier contrat", "Résilier contrat", "Enregistrer paiement", "Générer reçu", "Surveiller sécurité"]
        }
        
        for actor, permissions in actor_permissions.items():
            for permission in permissions:
                case_id = permission.replace(" ", "_").replace("é", "e").replace("è", "e")
                mermaid.append(f"    {actor} --> {case_id}")
        
        return "\n".join(mermaid)
    
    def generate_database_documentation(self):
        """Générer la documentation complète de la base de données"""
        print("📚 Génération de la documentation...")
        
        doc = []
        doc.append("# SCHÉMA DE BASE DE DONNÉES - KBIS INTERNATIONAL")
        doc.append(f"*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*")
        doc.append("")
        doc.append("## 📋 Vue d'ensemble")
        doc.append("")
        doc.append("Cette documentation présente la structure complète de la base de données de l'application KBIS INTERNATIONAL - Gestion Immobilière.")
        doc.append("")
        doc.append(f"**Nombre total de modèles:** {len(self.models)}")
        doc.append(f"**Nombre total de relations:** {len(self.relationships)}")
        doc.append("")
        
        # Par application
        for app_name, app_info in self.apps_info.items():
            doc.append(f"## 📱 {app_info['verbose_name']} ({app_name})")
            doc.append("")
            
            for model_name, model_info in app_info['models'].items():
                doc.append(f"### {model_info['verbose_name']} (`{model_name}`)")
                doc.append("")
                doc.append(f"**Description:** {model_info['verbose_name_plural']}")
                doc.append("")
                
                # Champs
                doc.append("#### Champs")
                doc.append("")
                doc.append("| Nom | Type | Description | Null | Unique | Défaut |")
                doc.append("|-----|------|-------------|------|--------|--------|")
                
                for field in model_info['fields']:
                    null_str = "✅" if field['null'] else "❌"
                    unique_str = "✅" if field['unique'] else "❌"
                    default_str = field['default'] if field['default'] else "-"
                    
                    doc.append(f"| `{field['name']}` | {field['type']} | {field['verbose_name']} | {null_str} | {unique_str} | {default_str} |")
                
                doc.append("")
                
                # Relations
                if model_info['relationships']:
                    doc.append("#### Relations")
                    doc.append("")
                    for rel in model_info['relationships']:
                        to_model = rel['to_model'].split('.')[-1]
                        doc.append(f"- **{rel['field_name']}:** {rel['relation_type']} vers `{to_model}`")
                    doc.append("")
                
                doc.append("---")
                doc.append("")
        
        return "\n".join(doc)
    
    def generate_migration_guide(self):
        """Générer un guide de migration"""
        print("🔄 Génération du guide de migration...")
        
        guide = []
        guide.append("# GUIDE DE MIGRATION - KBIS INTERNATIONAL")
        guide.append("")
        guide.append("## 🚀 Commandes de migration")
        guide.append("")
        guide.append("### Créer une nouvelle migration")
        guide.append("```bash")
        guide.append("python manage.py makemigrations")
        guide.append("```")
        guide.append("")
        guide.append("### Appliquer les migrations")
        guide.append("```bash")
        guide.append("python manage.py migrate")
        guide.append("```")
        guide.append("")
        guide.append("### Voir l'état des migrations")
        guide.append("```bash")
        guide.append("python manage.py showmigrations")
        guide.append("```")
        guide.append("")
        guide.append("### Annuler une migration")
        guide.append("```bash")
        guide.append("python manage.py migrate <app_name> <migration_number>")
        guide.append("```")
        guide.append("")
        guide.append("## 📋 Checklist avant migration")
        guide.append("")
        guide.append("- [ ] Sauvegarder la base de données")
        guide.append("- [ ] Tester en environnement de développement")
        guide.append("- [ ] Vérifier les contraintes de clés étrangères")
        guide.append("- [ ] Documenter les changements")
        guide.append("- [ ] Informer l'équipe")
        guide.append("")
        guide.append("## ⚠️ Points d'attention")
        guide.append("")
        guide.append("### Modèles avec suppression logique")
        guide.append("- `Utilisateur` (is_deleted)")
        guide.append("- `Propriete` (is_deleted)")
        guide.append("- `Bailleur` (is_deleted)")
        guide.append("- `Locataire` (is_deleted)")
        guide.append("")
        guide.append("### Relations critiques")
        guide.append("- `Contrat` → `Propriete` (PROTECT)")
        guide.append("- `Contrat` → `Locataire` (PROTECT)")
        guide.append("- `Paiement` → `Contrat` (PROTECT)")
        guide.append("")
        
        return "\n".join(guide)
    
    def save_diagrams(self):
        """Sauvegarder tous les diagrammes et la documentation"""
        print("💾 Sauvegarde des fichiers...")
        
        # Diagramme de classes
        class_diagram = self.generate_mermaid_class_diagram()
        with open('BD/diagramme_classes.md', 'w', encoding='utf-8') as f:
            f.write("# DIAGRAMME DE CLASSES - KBIS INTERNATIONAL\n\n")
            f.write("```mermaid\n")
            f.write(class_diagram)
            f.write("\n```")
        
        # Diagramme de cas d'utilisation
        use_case_diagram = self.generate_use_case_diagram()
        with open('BD/diagramme_cas_utilisation.md', 'w', encoding='utf-8') as f:
            f.write("# DIAGRAMME DE CAS D'UTILISATION - KBIS INTERNATIONAL\n\n")
            f.write("```mermaid\n")
            f.write(use_case_diagram)
            f.write("\n```")
        
        # Documentation complète
        documentation = self.generate_database_documentation()
        with open('BD/documentation_base_donnees.md', 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        # Guide de migration
        migration_guide = self.generate_migration_guide()
        with open('BD/guide_migration.md', 'w', encoding='utf-8') as f:
            f.write(migration_guide)
        
        # Schéma JSON pour outils externes
        schema_data = {
            'generated_at': datetime.now().isoformat(),
            'models': self.models,
            'relationships': self.relationships,
            'apps': self.apps_info
        }
        
        with open('BD/schema_complet.json', 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Fichiers sauvegardés dans le dossier BD/")
        print("📁 Fichiers générés:")
        print("   - diagramme_classes.md")
        print("   - diagramme_cas_utilisation.md")
        print("   - documentation_base_donnees.md")
        print("   - guide_migration.md")
        print("   - schema_complet.json")
    
    def run(self):
        """Exécuter la génération complète"""
        print("🚀 GÉNÉRATION DU SCHÉMA DE BASE DE DONNÉES KBIS INTERNATIONAL")
        print("=" * 70)
        
        self.analyze_models()
        self.save_diagrams()
        
        print("\n🎉 GÉNÉRATION TERMINÉE !")
        print("📊 Schéma complet disponible dans le dossier BD/")


if __name__ == "__main__":
    generator = DatabaseSchemaGenerator()
    generator.run()
