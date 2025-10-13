#!/usr/bin/env python
"""
Script de test pour vérifier la génération des documents KBIS
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement, QuittancePaiement
from document_kbis_unifie import DocumentKBISUnifie


def test_document_generation():
    """Test la génération de documents"""
    print("=== TEST DE GÉNÉRATION DE DOCUMENTS KBIS ===\n")
    
    # Test 1: Test direct de la classe DocumentKBISUnifie
    print("1. Test direct de DocumentKBISUnifie...")
    try:
        donnees_test = {
            'numero': 'QUI-20250101120000-TEST',
            'date': '01-Jan-25',
            'code_location': 'CTN012',
            'recu_de': 'Test Locataire',
            'mois_regle': 'janvier 2025',
            'type_paiement': 'caution',
            'mode_paiement': 'Espèces',
            'montant': 300000.00,
        }
        
        html = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'quittance_caution')
        if html:
            print("[OK] Document genere avec succes!")
            # Sauvegarder pour vérification
            with open('test_quittance_caution.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("   Document sauvegarde dans test_quittance_caution.html")
        else:
            print("[ERREUR] Erreur lors de la generation du document")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 2: Test avec un paiement existant
    print("2. Test avec un paiement existant...")
    try:
        # Récupérer le premier paiement valide
        paiement = Paiement.objects.filter(statut='valide').first()
        if paiement:
            print(f"   Paiement trouvé: {paiement.id} - {paiement.montant} F CFA")
            
            # Tester la génération de quittance
            html_quittance = paiement.generer_quittance_kbis_dynamique()
            if html_quittance:
                print("[OK] Quittance generee avec succes!")
                with open('test_quittance_reelle.html', 'w', encoding='utf-8') as f:
                    f.write(html_quittance)
                print("   Quittance sauvegardee dans test_quittance_reelle.html")
            else:
                print("[ERREUR] Erreur lors de la generation de la quittance")
                
            # Tester la génération de récépissé
            html_recu = paiement._generer_recu_kbis_dynamique()
            if html_recu:
                print("[OK] Recepisse genere avec succes!")
                with open('test_recu_reel.html', 'w', encoding='utf-8') as f:
                    f.write(html_recu)
                print("   Recepisse sauvegarde dans test_recu_reel.html")
            else:
                print("[ERREUR] Erreur lors de la generation du recepisse")
        else:
            print("[ATTENTION] Aucun paiement valide trouve dans la base de donnees")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 3: Test des différents types de documents
    print("3. Test des différents types de documents...")
    types_documents = [
        ('quittance_loyer', 'QUITTANCE DE LOYER'),
        ('quittance_caution', 'QUITTANCE DE CAUTION'),
        ('quittance_avance', 'QUITTANCE D\'AVANCE'),
        ('recu_loyer', 'RÉCÉPISSÉ DE LOYER'),
        ('recu_caution', 'RÉCÉPISSÉ DE CAUTION'),
    ]
    
    for type_doc, titre in types_documents:
        try:
            donnees = {
                'numero': f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'date': datetime.now().strftime('%d-%b-%y'),
                'code_location': 'CTN-TEST',
                'recu_de': 'Test Locataire',
                'mois_regle': 'janvier 2025',
                'type_paiement': type_doc.replace('quittance_', '').replace('recu_', ''),
                'mode_paiement': 'Espèces',
                'montant': 150000.00,
            }
            
            html = DocumentKBISUnifie.generer_document_unifie(donnees, type_doc)
            if html:
                print(f"[OK] {titre} genere avec succes")
            else:
                print(f"[ERREUR] Erreur pour {titre}")
        except Exception as e:
            print(f"[ERREUR] Erreur pour {titre}: {e}")
    
    print("\n=== FIN DES TESTS ===")


if __name__ == "__main__":
    test_document_generation()
