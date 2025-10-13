#!/usr/bin/env python
"""
Script de débogage pour vérifier le chemin de l'image d'en-tête
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from document_kbis_unifie import DocumentKBISUnifie


def debug_image_path():
    """Débogage du chemin de l'image d'en-tête"""
    print("=== DEBUG CHEMIN IMAGE D'ENTETE ===\n")
    
    # Test 1: Vérifier les chemins possibles
    print("1. Verification des chemins possibles...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"   Base directory: {base_dir}")
    
    possible_paths = [
        'static/images/enteteEnImage.png',
        'staticfiles/images/enteteEnImage.png',
        os.path.join(base_dir, 'static', 'images', 'enteteEnImage.png'),
        os.path.join(base_dir, 'staticfiles', 'images', 'enteteEnImage.png'),
        os.path.join(os.path.dirname(base_dir), 'static', 'images', 'enteteEnImage.png'),
        os.path.join(os.path.dirname(base_dir), 'staticfiles', 'images', 'enteteEnImage.png'),
    ]
    
    for i, path in enumerate(possible_paths, 1):
        exists = os.path.exists(path)
        print(f"   {i}. {path}: {'EXISTE' if exists else 'NON TROUVE'}")
        if exists:
            size = os.path.getsize(path)
            print(f"      Taille: {size} bytes")
    
    print()
    
    # Test 2: Test de la méthode _get_image_base64
    print("2. Test de la methode _get_image_base64...")
    try:
        image_base64 = DocumentKBISUnifie._get_image_base64()
        if image_base64:
            print("   [OK] Image convertie en base64")
            print(f"   Taille base64: {len(image_base64)} caracteres")
            print(f"   Debut: {image_base64[:50]}...")
        else:
            print("   [ERREUR] Aucune image trouvee")
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Test de génération de document
    print("3. Test de generation de document...")
    try:
        donnees_test = {
            'numero': 'DEBUG-20250113160000-TEST',
            'date': '13-Jan-25',
            'code_location': 'CTN-DEBUG',
            'recu_de': 'Test Debug',
            'mois_regle': 'janvier 2025',
            'type_paiement': 'loyer',
            'mode_paiement': 'Espèces',
            'montant': 150000.00,
        }
        
        html = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'quittance_loyer')
        if html:
            print("   [OK] Document genere")
            print(f"   Taille: {len(html)} caracteres")
            
            # Vérifier l'image
            if 'data:image/png;base64' in html:
                print("   [OK] Image base64 presente dans le document")
            else:
                print("   [ATTENTION] Image base64 manquante dans le document")
            
            # Sauvegarder pour inspection
            with open('debug_image_test.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("   Fichier sauvegarde: debug_image_test.html")
        else:
            print("   [ERREUR] Erreur generation document")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 4: Vérifier le répertoire de travail
    print("4. Verification du repertoire de travail...")
    print(f"   Repertoire courant: {os.getcwd()}")
    print(f"   Fichiers dans le repertoire courant:")
    try:
        files = os.listdir('.')
        for f in files[:10]:  # Afficher les 10 premiers
            if os.path.isfile(f):
                print(f"     - {f}")
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print("\n=== FIN DEBUG ===")


if __name__ == "__main__":
    debug_image_path()

