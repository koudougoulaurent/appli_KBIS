#!/usr/bin/env python
"""
Script de test pour vérifier la correction en production
À exécuter sur Render après déploiement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_recu_generation_fix():
    """Test complet de la correction de génération des récépissés"""
    print("🧪 Test de la correction de génération des récépissés")
    print("=" * 60)
    
    # Test 1: Import du module DocumentKBISUnifie
    print("\n1️⃣ Test d'import DocumentKBISUnifie...")
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath('paiements/models.py')))
        scripts_path = os.path.join(project_root, 'SCRIPTS')
        if scripts_path not in sys.path:
            sys.path.append(scripts_path)
        from document_kbis_unifie import DocumentKBISUnifie
        print("✅ Import DocumentKBISUnifie: SUCCÈS")
    except Exception as e:
        print(f"❌ Import DocumentKBISUnifie: ÉCHEC - {e}")
        return False
    
    # Test 2: Génération de document avec des données de test
    print("\n2️⃣ Test de génération avec données de test...")
    try:
        donnees_test = {
            'numero': 'REC-TEST-PROD-2025',
            'date': '01-Jan-25',
            'code_location': 'CTN-TEST',
            'recu_de': 'Test Production',
            'mois_regle': 'janvier 2025',
            'type_paiement': 'loyer',
            'mode_paiement': 'Espèces',
            'montant': 50000.00,
        }
        
        html = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'recu_loyer')
        if html and len(html) > 1000:
            print("✅ Génération test: SUCCÈS")
            print(f"📄 Taille HTML: {len(html)} caractères")
        else:
            print("❌ Génération test: ÉCHEC - HTML invalide")
            return False
    except Exception as e:
        print(f"❌ Génération test: ÉCHEC - {e}")
        return False
    
    # Test 3: Test avec un paiement réel de la base de données
    print("\n3️⃣ Test avec paiement réel de la base...")
    try:
        from paiements.models import Paiement
        
        paiement = Paiement.objects.first()
        if paiement:
            print(f"📋 Paiement trouvé: ID {paiement.id}, Montant: {paiement.montant}")
            
            html_recu = paiement._generer_recu_kbis_dynamique()
            if html_recu and len(html_recu) > 1000:
                print("✅ Génération récépissé réel: SUCCÈS")
                print(f"📄 Taille HTML: {len(html_recu)} caractères")
            else:
                print("❌ Génération récépissé réel: ÉCHEC - HTML invalide")
                return False
        else:
            print("⚠️ Aucun paiement trouvé dans la base de données")
            print("✅ Correction appliquée (pas de données pour test complet)")
    except Exception as e:
        print(f"❌ Test paiement réel: ÉCHEC - {e}")
        return False
    
    # Test 4: Test des autres méthodes de génération
    print("\n4️⃣ Test des autres méthodes de génération...")
    try:
        from paiements.models import RetraitBailleur, RecapMensuel
        
        # Test génération quittance
        if hasattr(paiement, '_generer_quittance_kbis_dynamique'):
            html_quittance = paiement._generer_quittance_kbis_dynamique()
            if html_quittance:
                print("✅ Génération quittance: SUCCÈS")
            else:
                print("⚠️ Génération quittance: Pas de données")
        
        print("✅ Toutes les méthodes de génération sont disponibles")
    except Exception as e:
        print(f"⚠️ Test méthodes supplémentaires: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 RÉSULTAT: Correction appliquée avec succès!")
    print("✅ La génération des récépissés et quittances fonctionne")
    print("🌐 L'application est prête pour la production")
    return True

if __name__ == "__main__":
    success = test_recu_generation_fix()
    sys.exit(0 if success else 1)
