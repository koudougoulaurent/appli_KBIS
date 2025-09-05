#!/usr/bin/env python
"""
Script pour remplacer automatiquement tous les "F CFA" par "F CFA" dans les templates HTML
"""

import os
import re
from pathlib import Path

def replace_xof_in_file(file_path):
    """Remplace F CFA par F CFA dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compter les occurrences avant remplacement
        count_before = content.count('F CFA')
        
        if count_before == 0:
            return 0
        
        # Remplacer F CFA par F CFA
        content = content.replace('F CFA', 'F CFA')
        
        # Écrire le fichier modifié
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Compter les occurrences après remplacement
        count_after = content.count('F CFA')
        
        print(f"✅ {file_path}: {count_before} F CFA → {count_after} F CFA")
        return count_before
        
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return 0

def replace_xof_in_templates():
    """Remplace F CFA par F CFA dans tous les templates HTML"""
    print("🔄 Remplacement automatique de F CFA vers F CFA dans les templates...")
    
    # Dossier des templates
    templates_dir = Path('templates')
    
    if not templates_dir.exists():
        print("❌ Dossier templates non trouvé")
        return
    
    total_replacements = 0
    files_modified = 0
    
    # Parcourir tous les fichiers HTML
    for html_file in templates_dir.rglob('*.html'):
        replacements = replace_xof_in_file(html_file)
        if replacements > 0:
            total_replacements += replacements
            files_modified += 1
    
    print(f"\n📊 Résumé:")
    print(f"   • Fichiers modifiés: {files_modified}")
    print(f"   • Total remplacements: {total_replacements}")
    print(f"   • F CFA → F CFA: {total_replacements}")
    
    return total_replacements

def replace_xof_in_static_files():
    """Remplace F CFA par F CFA dans les fichiers statiques (CSS, JS)"""
    print("\n🔄 Remplacement dans les fichiers statiques...")
    
    static_dir = Path('static')
    
    if not static_dir.exists():
        print("❌ Dossier static non trouvé")
        return 0
    
    total_replacements = 0
    files_modified = 0
    
    # Fichiers CSS et JS
    for ext in ['*.css', '*.js']:
        for file_path in static_dir.rglob(ext):
            replacements = replace_xof_in_file(file_path)
            if replacements > 0:
                total_replacements += replacements
                files_modified += 1
    
    print(f"📊 Fichiers statiques:")
    print(f"   • Fichiers modifiés: {files_modified}")
    print(f"   • Total remplacements: {total_replacements}")
    
    return total_replacements

def main():
    """Fonction principale"""
    print("🚀 Remplacement automatique F CFA → F CFA")
    print("=" * 50)
    
    # 1. Templates HTML
    template_replacements = replace_xof_in_templates()
    
    # 2. Fichiers statiques
    static_replacements = replace_xof_in_static_files()
    
    # 3. Résumé global
    total = template_replacements + static_replacements
    
    print(f"\n" + "=" * 50)
    print(f"✅ Remplacement terminé!")
    print(f"📊 Total global: {total} remplacements F CFA → F CFA")
    
    if total > 0:
        print(f"\n⚠️  Actions recommandées:")
        print(f"   • Redémarrer le serveur Django")
        print(f"   • Vider le cache du navigateur")
        print(f"   • Vérifier l'affichage des montants")
    
    return total > 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
