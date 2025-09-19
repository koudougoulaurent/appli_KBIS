#!/usr/bin/env python
"""
Générateur de schéma optimisé pour KBIS INTERNATIONAL
Génère automatiquement tous les fichiers de documentation et de schéma
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
from django.db import connection
import json
from datetime import datetime
import subprocess


class OptimizedSchemaGenerator:
    """Générateur de schéma optimisé"""
    
    def __init__(self):
        self.models = {}
        self.relationships = []
        self.apps_info = {}
        self.stats = {
            'apps_analyzed': 0,
            'models_analyzed': 0,
            'relationships_found': 0,
            'fields_analyzed': 0
        }
    
    def analyze_database(self):
        """Analyser la base de données complète"""
        print("🔍 Analyse de la base de données...")
        
        try:
            for app_config in apps.get_app_configs():
                if self._should_skip_app(app_config.name):
                    continue
                
                self._analyze_app(app_config)
            
            print(f"✅ Analyse terminée: {self.stats['models_analyzed']} modèles dans {self.stats['apps_analyzed']} applications")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def _should_skip_app(self, app_name):
        """Déterminer si une app doit être ignorée"""
        skip_apps = ['django.', 'admin', 'auth', 'contenttypes', 'sessions', 'migrations']
        return any(app_name.startswith(skip) for skip in skip_apps)
    
    def _analyze_app(self, app_config):
        """Analyser une application"""
        app_name = app_config.name
        print(f"📱 Application: {app_name}")
        
        self.apps_info[app_name] = {
            'verbose_name': app_config.verbose_name,
            'models': {}
        }
        self.stats['apps_analyzed'] += 1
        
        try:
            for model in app_config.get_models():
                self._analyze_model(model, app_name)
        except Exception as e:
            print(f"  ⚠️ Erreur lors de l'analyse de l'app {app_name}: {e}")
    
    def _analyze_model(self, model, app_name):
        """Analyser un modèle"""
        model_name = model.__name__
        print(f"  📋 Modèle: {model_name}")
        
        model_info = {
            'name': model_name,
            'app': app_name,
            'verbose_name': model._meta.verbose_name,
            'verbose_name_plural': model._meta.verbose_name_plural,
            'fields': [],
            'relationships': [],
            'meta': self._extract_meta_info(model)
        }
        
        # Analyser les champs
        for field in model._meta.get_fields():
            if hasattr(field, 'name'):
                field_info = self._analyze_field(field)
                model_info['fields'].append(field_info)
                self.stats['fields_analyzed'] += 1
                
                # Analyser les relations
                if hasattr(field, 'related_model') and field.related_model:
                    rel_info = self._analyze_relationship(field, model)
                    model_info['relationships'].append(rel_info)
                    self.relationships.append(rel_info)
                    self.stats['relationships_found'] += 1
        
        self.models[f"{app_name}.{model_name}"] = model_info
        self.apps_info[app_name]['models'][model_name] = model_info
        self.stats['models_analyzed'] += 1
    
    def _extract_meta_info(self, model):
        """Extraire les informations meta du modèle"""
        return {
            'ordering': getattr(model._meta, 'ordering', []),
            'unique_together': getattr(model._meta, 'unique_together', []),
            'index_together': getattr(model._meta, 'index_together', []),
            'db_table': model._meta.db_table,
            'managed': model._meta.managed,
            'abstract': model._meta.abstract
        }
    
    def _analyze_field(self, field):
        """Analyser un champ"""
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'verbose_name': getattr(field, 'verbose_name', field.name),
            'help_text': getattr(field, 'help_text', ''),
            'null': getattr(field, 'null', False),
            'blank': getattr(field, 'blank', False),
            'default': self._format_default_value(field),
            'max_length': getattr(field, 'max_length', None),
            'choices': getattr(field, 'choices', None),
            'unique': getattr(field, 'unique', False),
            'primary_key': getattr(field, 'primary_key', False),
            'db_index': getattr(field, 'db_index', False),
            'db_column': getattr(field, 'db_column', None)
        }
        return field_info
    
    def _format_default_value(self, field):
        """Formater la valeur par défaut d'un champ"""
        default = getattr(field, 'default', None)
        if default is None:
            return None
        elif callable(default):
            return f"<function {default.__name__}>"
        else:
            return str(default)
    
    def _analyze_relationship(self, field, model):
        """Analyser une relation"""
        return {
            'from_model': f"{model._meta.app_label}.{model.__name__}",
            'to_model': f"{field.related_model._meta.app_label}.{field.related_model.__name__}",
            'field_name': field.name,
            'relation_type': field.__class__.__name__,
            'related_name': getattr(field, 'related_name', None),
            'on_delete': str(getattr(field, 'on_delete', None)),
            'through': getattr(field, 'through', None),
            'symmetrical': getattr(field, 'symmetrical', None)
        }
    
    def generate_documentation(self):
        """Générer la documentation complète"""
        print("📚 Génération de la documentation...")
        
        # Documentation principale
        self._generate_main_documentation()
        
        # Diagrammes
        self._generate_diagrams()
        
        # Guide de migration
        self._generate_migration_guide()
        
        # Schéma JSON
        self._generate_json_schema()
        
        print("✅ Documentation générée avec succès")
    
    def _generate_main_documentation(self):
        """Générer la documentation principale"""
        doc_content = [
            "# 📊 DOCUMENTATION COMPLÈTE - KBIS INTERNATIONAL",
            f"*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*",
            "",
            "## 📋 Vue d'ensemble",
            "",
            f"**Nombre total de modèles:** {self.stats['models_analyzed']}",
            f"**Nombre total de relations:** {self.stats['relationships_found']}",
            f"**Nombre total de champs:** {self.stats['fields_analyzed']}",
            f"**Applications analysées:** {self.stats['apps_analyzed']}",
            "",
            "## 📱 Applications et modèles",
            ""
        ]
        
        for app_name, app_info in self.apps_info.items():
            doc_content.extend([
                f"### {app_info['verbose_name']} ({app_name})",
                "",
                f"**Description:** {app_info['verbose_name']}",
                f"**Modèles:** {len(app_info['models'])}",
                ""
            ])
            
            for model_name, model_info in app_info['models'].items():
                doc_content.extend([
                    f"#### {model_info['verbose_name']} (`{model_name}`)",
                    "",
                    f"**Description:** {model_info['verbose_name_plural']}",
                    f"**Champs:** {len(model_info['fields'])}",
                    f"**Relations:** {len(model_info['relationships'])}",
                    ""
                ])
                
                # Champs principaux
                doc_content.append("**Champs principaux:**")
                for field in model_info['fields'][:10]:
                    field_type = field['type'].replace('Field', '')
                    doc_content.append(f"- `{field['name']}` ({field_type}) - {field['verbose_name']}")
                
                if len(model_info['fields']) > 10:
                    doc_content.append(f"- ... et {len(model_info['fields']) - 10} autres champs")
                
                doc_content.append("")
        
        with open('BD/documentation_complete.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(doc_content))
    
    def _generate_diagrams(self):
        """Générer les diagrammes"""
        print("📊 Génération des diagrammes...")
        
        # Diagramme de classes
        self._generate_class_diagram()
        
        # Diagramme de cas d'utilisation
        self._generate_use_case_diagram()
    
    def _generate_class_diagram(self):
        """Générer le diagramme de classes"""
        mermaid_content = ["classDiagram"]
        
        for model_name, model_info in self.models.items():
            class_name = model_info['name']
            mermaid_content.append(f"    class {class_name} {{")
            
            # Champs principaux
            for field in model_info['fields'][:8]:
                field_type = field['type'].replace('Field', '').replace('Char', 'String')
                field_name = field['name']
                if field['primary_key']:
                    field_name = f"🔑 {field_name}"
                elif field['unique']:
                    field_name = f"🔒 {field_name}"
                
                mermaid_content.append(f"        +{field_name}: {field_type}")
            
            if len(model_info['fields']) > 8:
                mermaid_content.append(f"        +... {len(model_info['fields']) - 8} autres champs")
            
            mermaid_content.append("    }")
            mermaid_content.append("")
        
        # Relations
        for rel in self.relationships:
            from_class = rel['from_model'].split('.')[-1]
            to_class = rel['to_model'].split('.')[-1]
            
            if rel['relation_type'] == 'ForeignKey':
                mermaid_content.append(f"    {from_class} ||--o{{ {to_class} : {rel['field_name']}")
            elif rel['relation_type'] == 'OneToOneField':
                mermaid_content.append(f"    {from_class} ||--|| {to_class} : {rel['field_name']}")
            elif rel['relation_type'] == 'ManyToManyField':
                mermaid_content.append(f"    {from_class} ||--o{{ {to_class} : {rel['field_name']}")
        
        with open('BD/diagramme_classes_simple.md', 'w', encoding='utf-8') as f:
            f.write("# DIAGRAMME DE CLASSES - KBIS INTERNATIONAL\n\n")
            f.write("```mermaid\n")
            f.write('\n'.join(mermaid_content))
            f.write("\n```")
    
    def _generate_use_case_diagram(self):
        """Générer le diagramme de cas d'utilisation"""
        mermaid_content = ["graph TD"]
        
        # Acteurs
        mermaid_content.extend([
            "    Admin[👑 Administrateur]",
            "    Caisse[💰 Caissier]",
            "    Controle[🔍 Contrôleur]",
            "    Privilege[⭐ Utilisateur Privilégié]",
            ""
        ])
        
        # Cas d'utilisation
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
            ]
        }
        
        for module, cases in use_cases.items():
            mermaid_content.append(f"    subgraph {module}")
            for case in cases:
                case_id = case.replace(" ", "_").replace("é", "e").replace("è", "e")
                mermaid_content.append(f"        {case_id}[\"{case}\"]")
            mermaid_content.append("    end")
            mermaid_content.append("")
        
        with open('BD/diagramme_cas_utilisation.md', 'w', encoding='utf-8') as f:
            f.write("# DIAGRAMME DE CAS D'UTILISATION - KBIS INTERNATIONAL\n\n")
            f.write("```mermaid\n")
            f.write('\n'.join(mermaid_content))
            f.write("\n```")
    
    def _generate_migration_guide(self):
        """Générer le guide de migration"""
        guide_content = [
            "# 🔄 GUIDE DE MIGRATION - KBIS INTERNATIONAL",
            "",
            "## 🚀 Commandes essentielles",
            "",
            "### Créer une migration",
            "```bash",
            "python manage.py makemigrations",
            "```",
            "",
            "### Appliquer les migrations",
            "```bash",
            "python manage.py migrate",
            "```",
            "",
            "### Voir l'état des migrations",
            "```bash",
            "python manage.py showmigrations",
            "```",
            "",
            "## 📋 Checklist avant migration",
            "",
            "- [ ] Sauvegarder la base de données",
            "- [ ] Tester en environnement de développement",
            "- [ ] Vérifier les contraintes de clés étrangères",
            "- [ ] Documenter les changements",
            "- [ ] Informer l'équipe",
            "",
            "## ⚠️ Points d'attention",
            "",
            "### Modèles avec suppression logique",
            "- `Utilisateur` (is_deleted)",
            "- `Propriete` (is_deleted)",
            "- `Bailleur` (is_deleted)",
            "- `Locataire` (is_deleted)",
            "",
            "### Relations critiques",
            "- `Contrat` → `Propriete` (PROTECT)",
            "- `Contrat` → `Locataire` (PROTECT)",
            "- `Paiement` → `Contrat` (PROTECT)",
            ""
        ]
        
        with open('BD/guide_migration.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(guide_content))
    
    def _generate_json_schema(self):
        """Générer le schéma JSON"""
        schema_data = {
            'generated_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'description': 'Schéma complet de la base de données KBIS INTERNATIONAL',
            'statistics': self.stats,
            'models': self.models,
            'relationships': self.relationships,
            'apps': self.apps_info
        }
        
        with open('BD/schema_complet.json', 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
    
    def run(self):
        """Exécuter la génération complète"""
        print("🚀 GÉNÉRATION OPTIMISÉE DU SCHÉMA KBIS INTERNATIONAL")
        print("=" * 60)
        
        try:
            self.analyze_database()
            self.generate_documentation()
            
            print("\n🎉 GÉNÉRATION TERMINÉE !")
            print("📊 Statistiques finales:")
            for key, value in self.stats.items():
                print(f"   - {key}: {value}")
            print("\n📁 Fichiers générés dans BD/:")
            print("   - documentation_complete.md")
            print("   - diagramme_classes_simple.md")
            print("   - diagramme_cas_utilisation.md")
            print("   - guide_migration.md")
            print("   - schema_complet.json")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            sys.exit(1)


if __name__ == "__main__":
    generator = OptimizedSchemaGenerator()
    generator.run()