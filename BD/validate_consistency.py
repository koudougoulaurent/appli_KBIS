#!/usr/bin/env python
"""
Script de validation de la cohérence des fichiers du dossier BD
Vérifie que tous les fichiers sont cohérents entre eux
"""
import os
import json
import re
from datetime import datetime


class ConsistencyValidator:
    """Validateur de cohérence des fichiers BD"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.files_checked = []
    
    def validate_all(self):
        """Valider tous les fichiers"""
        print("🔍 VALIDATION DE LA COHÉRENCE - KBIS INTERNATIONAL")
        print("=" * 60)
        
        # Vérifier les fichiers essentiels
        self._check_essential_files()
        
        # Valider le schéma JSON
        self._validate_json_schema()
        
        # Valider les fichiers SQL
        self._validate_sql_files()
        
        # Valider la documentation
        self._validate_documentation()
        
        # Valider les scripts
        self._validate_scripts()
        
        # Afficher les résultats
        self._display_results()
    
    def _check_essential_files(self):
        """Vérifier la présence des fichiers essentiels"""
        print("📁 Vérification des fichiers essentiels...")
        
        essential_files = [
            'README.md',
            'SCHEMA_BDD_COMPLET.md',
            'schema_complet.json',
            'SCHEMA_MYSQL.sql',
            'SCHEMA_POSTGRESQL.sql',
            'SCHEMA_SQL_COMPLET.sql',
            'guide_migration.md',
            'simple_schema.py',
            'schema_base_donnees.py',
            'generate_schema.py',
            'generate_sql_other_dbms.py'
        ]
        
        for file in essential_files:
            if os.path.exists(file):
                self.files_checked.append(file)
                print(f"  ✅ {file}")
            else:
                self.errors.append(f"Fichier manquant: {file}")
                print(f"  ❌ {file} - MANQUANT")
    
    def _validate_json_schema(self):
        """Valider le schéma JSON"""
        print("\n📊 Validation du schéma JSON...")
        
        try:
            with open('schema_complet.json', 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Vérifier la structure
            required_keys = ['generated_at', 'models', 'relationships', 'apps']
            for key in required_keys:
                if key not in schema:
                    self.errors.append(f"Clé manquante dans schema_complet.json: {key}")
            
            # Vérifier les modèles
            if 'models' in schema:
                model_count = len(schema['models'])
                print(f"  📋 Modèles trouvés: {model_count}")
                
                if model_count == 0:
                    self.warnings.append("Aucun modèle trouvé dans le schéma JSON")
            
            # Vérifier les relations
            if 'relationships' in schema:
                rel_count = len(schema['relationships'])
                print(f"  🔗 Relations trouvées: {rel_count}")
            
            print("  ✅ Schéma JSON valide")
            
        except FileNotFoundError:
            self.errors.append("Fichier schema_complet.json non trouvé")
        except json.JSONDecodeError as e:
            self.errors.append(f"Erreur JSON dans schema_complet.json: {e}")
        except Exception as e:
            self.errors.append(f"Erreur lors de la validation du schéma JSON: {e}")
    
    def _validate_sql_files(self):
        """Valider les fichiers SQL"""
        print("\n🗄️ Validation des fichiers SQL...")
        
        sql_files = [
            'SCHEMA_MYSQL.sql',
            'SCHEMA_POSTGRESQL.sql',
            'SCHEMA_SQL_COMPLET.sql'
        ]
        
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                self._validate_sql_file(sql_file)
            else:
                self.errors.append(f"Fichier SQL manquant: {sql_file}")
    
    def _validate_sql_file(self, filename):
        """Valider un fichier SQL spécifique"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier la présence de CREATE TABLE
            create_tables = re.findall(r'CREATE TABLE\s+(\w+)', content, re.IGNORECASE)
            print(f"  📋 {filename}: {len(create_tables)} tables")
            
            # Vérifier la présence de commentaires
            if '--' not in content:
                self.warnings.append(f"Fichier {filename} ne contient pas de commentaires")
            
            # Vérifier la longueur du fichier
            if len(content) < 1000:
                self.warnings.append(f"Fichier {filename} semble trop court")
            
            print(f"  ✅ {filename} valide")
            
        except Exception as e:
            self.errors.append(f"Erreur lors de la validation de {filename}: {e}")
    
    def _validate_documentation(self):
        """Valider la documentation"""
        print("\n📚 Validation de la documentation...")
        
        doc_files = [
            'README.md',
            'SCHEMA_BDD_COMPLET.md',
            'guide_migration.md',
            'README_SQL.md'
        ]
        
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                self._validate_doc_file(doc_file)
            else:
                self.warnings.append(f"Fichier de documentation manquant: {doc_file}")
    
    def _validate_doc_file(self, filename):
        """Valider un fichier de documentation"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier la longueur
            if len(content) < 500:
                self.warnings.append(f"Fichier {filename} semble trop court")
            
            # Vérifier la présence de titres
            if '#' not in content:
                self.warnings.append(f"Fichier {filename} ne contient pas de titres Markdown")
            
            # Vérifier la présence de KBIS INTERNATIONAL
            if 'KBIS INTERNATIONAL' not in content:
                self.warnings.append(f"Fichier {filename} ne mentionne pas KBIS INTERNATIONAL")
            
            print(f"  ✅ {filename} valide")
            
        except Exception as e:
            self.errors.append(f"Erreur lors de la validation de {filename}: {e}")
    
    def _validate_scripts(self):
        """Valider les scripts Python"""
        print("\n🐍 Validation des scripts Python...")
        
        script_files = [
            'simple_schema.py',
            'schema_base_donnees.py',
            'generate_schema.py',
            'generate_sql_other_dbms.py'
        ]
        
        for script_file in script_files:
            if os.path.exists(script_file):
                self._validate_script_file(script_file)
            else:
                self.warnings.append(f"Script Python manquant: {script_file}")
    
    def _validate_script_file(self, filename):
        """Valider un script Python"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier la présence de shebang
            if not content.startswith('#!/usr/bin/env python'):
                self.warnings.append(f"Script {filename} ne commence pas par shebang")
            
            # Vérifier la présence de docstring
            if '"""' not in content:
                self.warnings.append(f"Script {filename} ne contient pas de docstring")
            
            # Vérifier la présence de gestion d'erreurs
            if 'try:' not in content and 'except' not in content:
                self.warnings.append(f"Script {filename} ne contient pas de gestion d'erreurs")
            
            print(f"  ✅ {filename} valide")
            
        except Exception as e:
            self.errors.append(f"Erreur lors de la validation de {filename}: {e}")
    
    def _display_results(self):
        """Afficher les résultats de la validation"""
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DE LA VALIDATION")
        print("=" * 60)
        
        print(f"\n📁 Fichiers vérifiés: {len(self.files_checked)}")
        print(f"❌ Erreurs: {len(self.errors)}")
        print(f"⚠️ Avertissements: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ ERREURS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️ AVERTISSEMENTS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 TOUS LES FICHIERS SONT COHÉRENTS !")
        elif not self.errors:
            print("\n✅ Aucune erreur critique, mais des avertissements à vérifier")
        else:
            print("\n❌ Des erreurs critiques ont été trouvées")
        
        print(f"\n📅 Validation effectuée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")


def main():
    """Fonction principale"""
    validator = ConsistencyValidator()
    validator.validate_all()


if __name__ == "__main__":
    main()
