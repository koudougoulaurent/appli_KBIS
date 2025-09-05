#!/usr/bin/env python
"""
Script pour remplacer automatiquement TOUS les "F CFA" par "F CFA" dans l'application
"""

import os
import re
import sys

def replace_xof_in_file(file_path):
    """Remplace F CFA par F CFA dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        count_before = content.count('F CFA')
        
        if count_before == 0:
            return 0
        
        # Remplacer F CFA par F CFA
        content = content.replace('F CFA', 'F CFA')
        
        # Vérifier le remplacement
        count_after = content.count('F CFA')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {file_path}: {count_before} F CFA → F CFA")
        return count_before
        
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return 0

def replace_xof_in_directory(directory, extensions):
    """Remplace F CFA par F CFA dans tous les fichiers d'un dossier"""
    total_replacements = 0
    files_modified = 0
    
    for root, dirs, files in os.walk(directory):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules', '.vscode']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                replacements = replace_xof_in_file(file_path)
                if replacements > 0:
                    total_replacements += replacements
                    files_modified += 1
    
    return total_replacements, files_modified

def main():
    """Fonction principale"""
    print("🔄 Remplacement Global F CFA → F CFA")
    print("=" * 60)
    
    # Vérifier qu'on est dans le bon dossier
    if not os.path.exists('manage.py'):
        print("❌ Ce script doit être exécuté depuis le dossier appli_KBIS")
        sys.exit(1)
    
    total_global = 0
    files_global = 0
    
    # 1. Templates HTML
    print("📄 Templates HTML...")
    replacements, files = replace_xof_in_directory('templates', ['.html'])
    total_global += replacements
    files_global += files
    print(f"   • {replacements} remplacements dans {files} fichiers")
    
    # 2. Modèles Python
    print("🐍 Modèles Python...")
    replacements, files = replace_xof_in_directory('.', ['.py'])
    total_global += replacements
    files_global += files
    print(f"   • {replacements} remplacements dans {files} fichiers")
    
    # 3. Fichiers statiques (JS, CSS)
    print("📁 Fichiers statiques...")
    replacements, files = replace_xof_in_directory('static', ['.js', '.css'])
    total_global += replacements
    files_global += files
    print(f"   • {replacements} remplacements dans {files} fichiers")
    
    # 4. Documentation Markdown
    print("📚 Documentation...")
    replacements, files = replace_xof_in_directory('.', ['.md'])
    total_global += replacements
    files_global += files
    print(f"   • {replacements} remplacements dans {files} fichiers")
    
    # 5. Fichiers de configuration
    print("⚙️ Configuration...")
    replacements, files = replace_xof_in_directory('.', ['.json', '.yml', '.yaml'])
    total_global += replacements
    files_global += files
    print(f"   • {replacements} remplacements dans {files} fichiers")
    
    print("\n" + "=" * 60)
    print(f"🎉 REMPLACEMENT TERMINÉ !")
    print(f"📊 Total : {total_global} remplacements F CFA → F CFA")
    print(f"📁 Fichiers modifiés : {files_global}")
    print("=" * 60)
    
    if total_global > 0:
        print("\n📋 Actions recommandées :")
        print("1. Tester l'application pour vérifier les changements")
        print("2. Créer une sauvegarde si tout fonctionne")
        print("3. Vérifier les PDFs et documents générés")
        print("4. Redémarrer le serveur Django")
    
    return total_global

if __name__ == "__main__":
    total = main()
    
    if total > 0:
        print(f"\n✅ {total} occurrences de F CFA remplacées par F CFA !")
        print("🔄 Redémarrez le serveur pour appliquer les changements.")
    else:
        print("\n✅ Aucun F CFA trouvé - tout est déjà en F CFA !")
