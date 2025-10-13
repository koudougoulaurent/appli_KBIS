#!/usr/bin/env python
"""
Script pour tester directement la génération de documents sans passer par les vues Django
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


def test_direct_document_generation():
    """Test direct de la génération de documents"""
    print("=== TEST DIRECT GENERATION DOCUMENTS ===\n")
    
    # Test 1: Génération directe avec paiement existant
    print("1. Generation directe avec paiement existant...")
    try:
        paiement = Paiement.objects.filter(statut='valide').first()
        if not paiement:
            print("   [ERREUR] Aucun paiement valide trouve")
            return
        
        print(f"   Paiement: ID {paiement.id} - {paiement.montant} F CFA")
        print(f"   Type: {paiement.type_paiement}")
        
        # Générer récépissé
        html_recu = paiement._generer_recu_kbis_dynamique()
        if html_recu:
            print("   [OK] Recepisse genere avec succes")
            print(f"   Taille: {len(html_recu)} caracteres")
            
            # Vérifier l'image
            if 'data:image/png;base64' in html_recu:
                print("   [OK] Image d'entete presente (base64)")
            else:
                print("   [ATTENTION] Image d'entete manquante")
            
            # Sauvegarder
            with open('test_direct_recu.html', 'w', encoding='utf-8') as f:
                f.write(html_recu)
            print("   Fichier sauvegarde: test_direct_recu.html")
        else:
            print("   [ERREUR] Erreur generation recepisse")
        
        # Générer quittance
        html_quittance = paiement.generer_quittance_kbis_dynamique()
        if html_quittance:
            print("   [OK] Quittance generee avec succes")
            print(f"   Taille: {len(html_quittance)} caracteres")
            
            # Vérifier l'image
            if 'data:image/png;base64' in html_quittance:
                print("   [OK] Image d'entete presente (base64)")
            else:
                print("   [ATTENTION] Image d'entete manquante")
            
            # Sauvegarder
            with open('test_direct_quittance.html', 'w', encoding='utf-8') as f:
                f.write(html_quittance)
            print("   Fichier sauvegarde: test_direct_quittance.html")
        else:
            print("   [ERREUR] Erreur generation quittance")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: Génération avec différents types de paiements
    print("2. Generation avec differents types de paiements...")
    try:
        types_paiements = ['loyer', 'caution', 'avance', 'depot_garantie']
        
        for type_paiement in types_paiements:
            print(f"   Test type: {type_paiement}")
            
            # Créer des données de test
            donnees_test = {
                'numero': f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}-{type_paiement.upper()}',
                'date': datetime.now().strftime('%d-%b-%y'),
                'code_location': f'CTN-{type_paiement.upper()}',
                'recu_de': f'Test {type_paiement.title()}',
                'mois_regle': datetime.now().strftime('%B %Y'),
                'type_paiement': type_paiement,
                'mode_paiement': 'Espèces',
                'montant': 200000.00,
            }
            
            # Générer récépissé
            type_recu = f'recu_{type_paiement}' if type_paiement != 'depot_garantie' else 'recu_caution'
            html_recu = DocumentKBISUnifie.generer_document_unifie(donnees_test, type_recu)
            
            if html_recu and 'data:image/png;base64' in html_recu:
                print(f"     [OK] Recepisse {type_paiement} avec image")
            else:
                print(f"     [ATTENTION] Probleme recepisse {type_paiement}")
            
            # Générer quittance
            type_quittance = f'quittance_{type_paiement}' if type_paiement != 'depot_garantie' else 'quittance_caution'
            html_quittance = DocumentKBISUnifie.generer_document_unifie(donnees_test, type_quittance)
            
            if html_quittance and 'data:image/png;base64' in html_quittance:
                print(f"     [OK] Quittance {type_paiement} avec image")
            else:
                print(f"     [ATTENTION] Probleme quittance {type_paiement}")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print()
    
    # Test 3: Créer un document de démonstration complet
    print("3. Creation document de demonstration complet...")
    try:
        # Document de démonstration avec toutes les informations
        donnees_demo = {
            'numero': 'DEMO-20250113160000-KBIS',
            'date': datetime.now().strftime('%d-%b-%y'),
            'code_location': 'CTN-DEMO-001',
            'recu_de': 'Client Demonstration KBIS',
            'mois_regle': datetime.now().strftime('%B %Y'),
            'type_paiement': 'loyer',
            'mode_paiement': 'Virement bancaire',
            'montant': 350000.00,
            'loyer_base': 300000.00,
            'charges_mensuelles': 50000.00,
            'total_mensuel': 350000.00,
        }
        
        # Générer les deux types de documents
        html_recu_demo = DocumentKBISUnifie.generer_document_unifie(donnees_demo, 'recu_loyer')
        html_quittance_demo = DocumentKBISUnifie.generer_document_unifie(donnees_demo, 'quittance_loyer')
        
        if html_recu_demo and 'data:image/png;base64' in html_recu_demo:
            with open('demo_recu_complet.html', 'w', encoding='utf-8') as f:
                f.write(html_recu_demo)
            print("   [OK] Demo recepisse complet genere")
        else:
            print("   [ATTENTION] Probleme demo recepisse")
        
        if html_quittance_demo and 'data:image/png;base64' in html_quittance_demo:
            with open('demo_quittance_complet.html', 'w', encoding='utf-8') as f:
                f.write(html_quittance_demo)
            print("   [OK] Demo quittance complete generee")
        else:
            print("   [ATTENTION] Probleme demo quittance")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print("\n=== FIN TESTS DIRECTS ===")
    print("\nFICHIERS GENERES:")
    print("- test_direct_recu.html")
    print("- test_direct_quittance.html")
    print("- demo_recu_complet.html")
    print("- demo_quittance_complet.html")
    print("\nOuvrez ces fichiers dans votre navigateur pour voir le rendu final avec l'image d'entete!")


if __name__ == "__main__":
    test_direct_document_generation()
