#!/usr/bin/env python3
"""
Test simple pour vérifier que les fichiers de correction existent
"""

import os

def test_files():
    """Teste que les fichiers de correction existent"""
    
    print("🧪 Test des fichiers de correction")
    print("=" * 50)
    
    files_to_check = [
        "static/css/fix_select_display.css",
        "static/js/fix_select_display.js",
        "test_select_fix.html",
    ]
    
    all_exist = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} existe")
        else:
            print(f"❌ {file_path} manquant")
            all_exist = False
    
    return all_exist

def main():
    """Fonction principale"""
    
    print("🚀 TEST DES FICHIERS DE CORRECTION")
    print("=" * 50)
    
    if test_files():
        print("\n✅ TOUS LES FICHIERS EXISTENT!")
        print("🎉 Les corrections sont en place.")
        return 0
    else:
        print("\n❌ CERTAINS FICHIERS MANQUENT!")
        print("🔧 Veuillez créer les fichiers manquants.")
        return 1

if __name__ == "__main__":
    exit(main())
