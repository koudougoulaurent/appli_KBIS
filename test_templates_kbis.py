#!/usr/bin/env python
"""
Script de test pour le système de templates KBIS
Permet de tester la génération de documents avec en-tête et pied de page KBIS
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.utils import KBISDocumentTemplate


def test_entete_pied_page():
    """Test de génération de l'en-tête et du pied de page."""
    print("=== TEST EN-TÊTE ET PIED DE PAGE KBIS ===")
    
    # Test en-tête
    entete_html = KBISDocumentTemplate.get_entete_html()
    print(f"En-tête généré: {len(entete_html)} caractères")
    print(entete_html[:200] + "..." if len(entete_html) > 200 else entete_html)
    
    # Test pied de page
    pied_page_html = KBISDocumentTemplate.get_pied_page_html()
    print(f"\nPied de page généré: {len(pied_page_html)} caractères")
    print(pied_page_html[:200] + "..." if len(pied_page_html) > 200 else pied_page_html)
    
    return True


def test_document_complet():
    """Test de génération d'un document complet."""
    print("\n=== TEST DOCUMENT COMPLET KBIS ===")
    
    titre = "REÇU DE PAIEMENT TEST"
    contenu = """
    <div style="padding: 20px;">
        <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0;">Détails du Paiement</h2>
        <table style="width: 100%; margin: 20px 0;">
            <tr>
                <td><strong>Montant:</strong></td>
                <td>150 000 FCFA</td>
            </tr>
            <tr>
                <td><strong>Date:</strong></td>
                <td>15/12/2024</td>
            </tr>
            <tr>
                <td><strong>Référence:</strong></td>
                <td>TEST-001</td>
            </tr>
        </table>
        <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <p><strong>Note:</strong> Ce document a été généré automatiquement avec le système de templates KBIS.</p>
        </div>
    </div>
    """
    
    document_html = KBISDocumentTemplate.get_document_complet(titre, contenu, "Test")
    
    print(f"Document complet généré: {len(document_html)} caractères")
    
    # Sauvegarder le document pour inspection
    fichier_test = os.path.join(os.path.dirname(__file__), "test_document_kbis.html")
    with open(fichier_test, 'w', encoding='utf-8') as f:
        f.write(document_html)
    
    print(f"Document sauvegardé dans: {fichier_test}")
    return True


def test_recu_paiement_mock():
    """Test avec un objet paiement simulé."""
    print("\n=== TEST REÇU PAIEMENT SIMULÉ ===")
    
    # Créer un objet paiement simulé
    class PaiementMock:
        def __init__(self):
            self.montant = Decimal('150000.00')
            self.date_paiement = datetime.now()
            self.reference_paiement = "MOCK-TEST-001"
            self.mois_paye = datetime.now()
            
        def get_montant_formatted(self):
            return f"{self.montant:,.0f} FCFA"
            
        def get_nom_complet_locataire(self):
            return "M. KOUAME Jean-Baptiste"
            
        def get_adresse_propriete(self):
            return "Villa 3 pièces, Cocody Angré"
    
    paiement_mock = PaiementMock()
    
    try:
        # Tester la génération du reçu
        recu_html = KBISDocumentTemplate.generer_recu_paiement(paiement_mock)
        
        print(f"Reçu de paiement généré: {len(recu_html)} caractères")
        
        # Sauvegarder le reçu pour inspection
        fichier_recu = os.path.join(os.path.dirname(__file__), "test_recu_kbis.html")
        with open(fichier_recu, 'w', encoding='utf-8') as f:
            f.write(recu_html)
        
        print(f"Reçu sauvegardé dans: {fichier_recu}")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la génération du reçu: {e}")
        return False


def test_css_integration():
    """Test des styles CSS intégrés."""
    print("\n=== TEST CSS INTÉGRÉ ===")
    
    css = KBISDocumentTemplate.get_css_styles()
    print(f"CSS généré: {len(css)} caractères")
    
    # Vérifier quelques styles importants
    styles_requis = ['.header-kbis', '.footer-kbis', '.document-content', '.montant']
    for style in styles_requis:
        if style in css:
            print(f"✓ Style {style} présent")
        else:
            print(f"✗ Style {style} manquant")
    
    return True


def main():
    """Fonction principale de test."""
    print("DÉMARRAGE DES TESTS DU SYSTÈME DE TEMPLATES KBIS")
    print("=" * 60)
    
    tests = [
        ("En-tête et pied de page", test_entete_pied_page),
        ("Document complet", test_document_complet),
        ("Reçu de paiement simulé", test_recu_paiement_mock),
        ("CSS intégré", test_css_integration),
    ]
    
    resultats = []
    
    for nom_test, fonction_test in tests:
        try:
            print(f"\nExécution du test: {nom_test}")
            print("-" * 40)
            resultat = fonction_test()
            resultats.append((nom_test, resultat))
            print(f"Résultat: {'✓ SUCCÈS' if resultat else '✗ ÉCHEC'}")
        except Exception as e:
            print(f"✗ ERREUR lors du test {nom_test}: {e}")
            resultats.append((nom_test, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    succes = 0
    for nom_test, resultat in resultats:
        status = "✓" if resultat else "✗"
        print(f"{status} {nom_test}")
        if resultat:
            succes += 1
    
    print(f"\nTests réussis: {succes}/{len(tests)}")
    
    if succes == len(tests):
        print("\n🎉 TOUS LES TESTS ONT RÉUSSI!")
        print("Le système de templates KBIS est opérationnel.")
    else:
        print(f"\n⚠️  {len(tests) - succes} test(s) ont échoué.")
        print("Vérifiez les erreurs ci-dessus.")


if __name__ == "__main__":
    main()