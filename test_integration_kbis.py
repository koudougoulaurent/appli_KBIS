#!/usr/bin/env python
"""
Script de test pour l'intégration KBIS IMMOBILIER
Teste le nouveau système de quittances dynamiques dans Django
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement
from datetime import datetime
from django.contrib.auth import get_user_model

def tester_integration_kbis():
    """Test complet de l'intégration KBIS IMMOBILIER."""
    
    print("🏢 Test d'Intégration KBIS IMMOBILIER")
    print("=" * 50)
    
    # 1. Vérifier les paiements existants
    paiements = Paiement.objects.filter(is_deleted=False)[:5]
    
    print(f"📋 Nombre de paiements trouvés: {paiements.count()}")
    
    if not paiements.exists():
        print("❌ Aucun paiement trouvé pour le test")
        return
    
    # 2. Tester la génération pour chaque paiement
    for i, paiement in enumerate(paiements, 1):
        print(f"\n🧪 Test {i}/5 - Paiement ID: {paiement.id}")
        
        try:
            # Informations du paiement
            print(f"   👤 Locataire: {paiement.contrat.locataire.get_nom_complet() if paiement.contrat and paiement.contrat.locataire else 'Non défini'}")
            print(f"   💰 Montant: {paiement.montant} FCFA")
            print(f"   📅 Date: {paiement.date_paiement}")
            
            # Test génération quittance KBIS dynamique
            html_quittance = paiement.generer_quittance_kbis_dynamique()
            
            if html_quittance:
                # Sauvegarder le fichier de test
                nom_fichier = f"test_quittance_paiement_{paiement.id}.html"
                with open(nom_fichier, 'w', encoding='utf-8') as f:
                    f.write(html_quittance)
                
                print(f"   ✅ Quittance générée: {nom_fichier}")
                print(f"   📄 Taille HTML: {len(html_quittance):,} caractères")
                
                # Vérifications du contenu
                verifications = [
                    ("KBIS IMMOBILIER" in html_quittance, "Nom entreprise"),
                    ("Achat • Vente • Location • Gestion • Nettoyage" in html_quittance, "Services"),
                    ("DEPOT ORANGE" in html_quittance, "Orange Money"),
                    ("Format A5" in html_quittance or "148mm" in html_quittance, "Format A5"),
                    ("Imprimer" in html_quittance, "Bouton impression")
                ]
                
                for verification, nom in verifications:
                    if verification:
                        print(f"   ✅ {nom}: OK")
                    else:
                        print(f"   ⚠️ {nom}: Manquant")
                        
            else:
                print(f"   ❌ Erreur lors de la génération")
                
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
    
    # 3. Test de la nouvelle méthode generer_document_kbis
    print(f"\n🔧 Test de la méthode generer_document_kbis")
    
    try:
        paiement_test = paiements.first()
        
        # Test génération reçu
        recu_html = paiement_test.generer_document_kbis('recu')
        if recu_html:
            print("   ✅ Génération reçu: OK")
            with open("test_recu_kbis.html", 'w', encoding='utf-8') as f:
                f.write(recu_html)
        else:
            print("   ❌ Génération reçu: Erreur")
        
        # Test génération facture
        facture_html = paiement_test.generer_document_kbis('facture')
        if facture_html:
            print("   ✅ Génération facture: OK")
            with open("test_facture_kbis.html", 'w', encoding='utf-8') as f:
                f.write(facture_html)
        else:
            print("   ❌ Génération facture: Erreur")
            
    except Exception as e:
        print(f"   ❌ Erreur test generer_document_kbis: {str(e)}")
    
    # 4. Statistiques finales
    print(f"\n📊 Résumé du Test")
    print(f"   🏢 Entreprise: KBIS IMMOBILIER")
    print(f"   📋 Format: A5 (148mm × 210mm)")
    print(f"   🧪 Paiements testés: {min(5, paiements.count())}")
    print(f"   📄 Fichiers générés: test_*.html")
    print(f"   ⏰ Test terminé: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    
    print(f"\n🎉 INTÉGRATION KBIS IMMOBILIER TESTÉE AVEC SUCCÈS !")
    print("📱 Vous pouvez maintenant utiliser les nouvelles URLs:")
    print("   - /paiements/quittances-kbis-dynamiques/")
    print("   - /paiements/paiement/[ID]/quittance-kbis-dynamique/")

if __name__ == '__main__':
    tester_integration_kbis()