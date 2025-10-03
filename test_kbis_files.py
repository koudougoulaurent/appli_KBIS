#!/usr/bin/env python
"""
Script simple pour vérifier que les fichiers KBIS sont bien créés
"""
import os

def check_file_exists(file_path):
    """Vérifie si un fichier existe"""
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
        return True
    else:
        print(f"❌ {file_path}")
        return False

def main():
    """Fonction principale"""
    print("🔍 Vérification des fichiers KBIS")
    print("=" * 50)
    
    files_to_check = [
        # Templates HTML
        'templates/includes/kbis_header.html',
        'templates/includes/kbis_footer.html',
        'templates/includes/kbis_pdf_header.html',
        'templates/includes/kbis_pdf_footer.html',
        'templates/demo_kbis_design.html',
        
        # Styles CSS
        'static/css/kbis_header_footer.css',
        'static/css/kbis_pdf_styles.css',
        
        # Code Python
        'core/demo_views.py',
        'core/utils.py',
        
        # Documentation
        'KBIS_DESIGN_DOCUMENTATION.md',
        'test_kbis_design.py',
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if not check_file_exists(file_path):
            all_exist = False
    
    print("\n" + "=" * 50)
    if all_exist:
        print("✅ Tous les fichiers KBIS sont présents!")
        print("\n🎯 Pour tester le design :")
        print("1. Démarrez le serveur Django")
        print("2. Accédez à /demo-kbis-design/")
        print("3. Vérifiez l'affichage des en-têtes et pieds de page")
    else:
        print("❌ Certains fichiers sont manquants!")
    
    return all_exist

if __name__ == '__main__':
    main()
