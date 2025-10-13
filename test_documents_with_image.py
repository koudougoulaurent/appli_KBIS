#!/usr/bin/env python
"""
Script pour tester l'affichage des documents avec l'image d'en-tête
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement
from document_kbis_unifie import DocumentKBISUnifie


def test_documents_with_image():
    """Test l'affichage des documents avec l'image d'en-tête"""
    print("=== TEST DOCUMENTS AVEC IMAGE D'ENTETE ===\n")
    
    # Test 1: Document de test avec image
    print("1. Generation document de test avec image d'entete...")
    try:
        donnees_test = {
            'numero': 'QUI-20250113160000-TEST',
            'date': '13-Jan-25',
            'code_location': 'CTN-TEST',
            'recu_de': 'Test Locataire',
            'mois_regle': 'janvier 2025',
            'type_paiement': 'caution',
            'mode_paiement': 'Espèces',
            'montant': 300000.00,
        }
        
        html = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'quittance_caution')
        if html:
            print("[OK] Document genere avec image d'entete")
            
            # Sauvegarder pour test
            with open('test_document_avec_image.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("   Document sauvegarde: test_document_avec_image.html")
            
            # Vérifier que l'image est bien référencée
            if 'enteteEnImage.png' in html:
                print("   [OK] Image d'entete referencee correctement")
            else:
                print("   [ATTENTION] Image d'entete non trouvee dans le HTML")
        else:
            print("[ERREUR] Erreur lors de la generation du document")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 2: Document avec paiement réel
    print("2. Generation document avec paiement reel...")
    try:
        paiement = Paiement.objects.filter(statut='valide').first()
        if paiement:
            print(f"   Paiement: ID {paiement.id} - {paiement.montant} F CFA")
            
            # Générer quittance
            html_quittance = paiement.generer_quittance_kbis_dynamique()
            if html_quittance:
                print("[OK] Quittance generee avec image d'entete")
                
                with open('test_quittance_avec_image.html', 'w', encoding='utf-8') as f:
                    f.write(html_quittance)
                print("   Quittance sauvegarde: test_quittance_avec_image.html")
                
                # Vérifier l'image
                if 'enteteEnImage.png' in html_quittance:
                    print("   [OK] Image d'entete presente dans la quittance")
                else:
                    print("   [ATTENTION] Image d'entete manquante")
            else:
                print("[ERREUR] Erreur generation quittance")
        else:
            print("[ATTENTION] Aucun paiement valide trouve")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 3: Vérifier les chemins d'images
    print("3. Verification des chemins d'images...")
    try:
        image_path = "static/images/enteteEnImage.png"
        if os.path.exists(image_path):
            print(f"[OK] Image trouvee: {image_path}")
            print(f"   Taille: {os.path.getsize(image_path)} bytes")
        else:
            print(f"[ERREUR] Image non trouvee: {image_path}")
            
        # Vérifier les autres images disponibles
        images_dir = "static/images"
        if os.path.exists(images_dir):
            images = os.listdir(images_dir)
            print(f"   Images disponibles dans {images_dir}:")
            for img in images:
                if img.endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    print(f"     - {img}")
        else:
            print(f"[ERREUR] Dossier images non trouve: {images_dir}")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 4: Créer un document de démonstration
    print("4. Creation document de demonstration...")
    try:
        # Document de démonstration avec toutes les informations
        donnees_demo = {
            'numero': 'DEMO-20250113160000-KBIS',
            'date': datetime.now().strftime('%d-%b-%y'),
            'code_location': 'CTN-DEMO',
            'recu_de': 'Client Demonstration',
            'mois_regle': datetime.now().strftime('%B %Y'),
            'type_paiement': 'loyer',
            'mode_paiement': 'Virement bancaire',
            'montant': 250000.00,
            'loyer_base': 200000.00,
            'charges_mensuelles': 50000.00,
            'total_mensuel': 250000.00,
        }
        
        html_demo = DocumentKBISUnifie.generer_document_unifie(donnees_demo, 'quittance_loyer')
        if html_demo:
            print("[OK] Document de demonstration genere")
            
            with open('demo_quittance_avec_image.html', 'w', encoding='utf-8') as f:
                f.write(html_demo)
            print("   Document demo sauvegarde: demo_quittance_avec_image.html")
            
            # Instructions pour l'utilisateur
            print("\n   INSTRUCTIONS POUR TESTER:")
            print("   1. Ouvrez le fichier 'demo_quittance_avec_image.html' dans votre navigateur")
            print("   2. Verifiez que l'image d'entete s'affiche correctement")
            print("   3. Testez l'impression (Ctrl+P) pour voir le rendu final")
        else:
            print("[ERREUR] Erreur generation document demo")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print("\n=== FIN DES TESTS ===")


if __name__ == "__main__":
    test_documents_with_image()

