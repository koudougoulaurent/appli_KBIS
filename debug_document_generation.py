#!/usr/bin/env python
"""
Script de débogage pour la génération de documents
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


def debug_document_generation():
    """Débogage de la génération de documents"""
    print("=== DEBUG GENERATION DOCUMENTS ===\n")
    
    # Test 1: Test direct de la méthode du modèle
    print("1. Test direct methode du modele...")
    try:
        paiement = Paiement.objects.filter(statut='valide').first()
        if paiement:
            print(f"   Paiement: ID {paiement.id}")
            print(f"   Type: {paiement.type_paiement}")
            print(f"   Montant: {paiement.montant}")
            
            # Test de la méthode _generer_recu_kbis_dynamique
            html_recu = paiement._generer_recu_kbis_dynamique()
            if html_recu:
                print("   [OK] Methode _generer_recu_kbis_dynamique fonctionne")
                print(f"   Taille HTML: {len(html_recu)} caracteres")
                
                # Vérifier l'image
                if 'enteteEnImage.png' in html_recu:
                    print("   [OK] Image d'entete presente")
                else:
                    print("   [ATTENTION] Image d'entete manquante")
                
                # Sauvegarder pour inspection
                with open('debug_recu_direct.html', 'w', encoding='utf-8') as f:
                    f.write(html_recu)
                print("   Fichier sauvegarde: debug_recu_direct.html")
            else:
                print("   [ERREUR] Methode _generer_recu_kbis_dynamique retourne None")
        else:
            print("   [ERREUR] Aucun paiement valide trouve")
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: Test direct de DocumentKBISUnifie
    print("2. Test direct DocumentKBISUnifie...")
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
        
        html = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'recu_loyer')
        if html:
            print("   [OK] DocumentKBISUnifie fonctionne")
            print(f"   Taille HTML: {len(html)} caracteres")
            
            # Vérifier l'image
            if 'enteteEnImage.png' in html:
                print("   [OK] Image d'entete presente")
            else:
                print("   [ATTENTION] Image d'entete manquante")
            
            # Sauvegarder pour inspection
            with open('debug_document_unifie.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("   Fichier sauvegarde: debug_document_unifie.html")
        else:
            print("   [ERREUR] DocumentKBISUnifie retourne None")
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Vérifier le contenu des fichiers générés
    print("3. Verification contenu des fichiers...")
    try:
        files_to_check = [
            'debug_recu_direct.html',
            'debug_document_unifie.html',
            'test_recepisse_web.html'
        ]
        
        for filename in files_to_check:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"   {filename}:")
                print(f"     Taille: {len(content)} caracteres")
                print(f"     Contient 'enteteEnImage.png': {'enteteEnImage.png' in content}")
                print(f"     Contient 'KBIS': {'KBIS' in content}")
                print(f"     Contient 'DOCTYPE': {'DOCTYPE' in content}")
                
                # Vérifier les premières lignes
                lines = content.split('\n')[:5]
                print(f"     Premiere ligne: {lines[0] if lines else 'Vide'}")
            else:
                print(f"   {filename}: Fichier non trouve")
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print("\n=== FIN DEBUG ===")


if __name__ == "__main__":
    debug_document_generation()

