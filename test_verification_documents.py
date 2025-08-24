#!/usr/bin/env python3
"""
Script de Test du Système de Vérification de Véracité des Documents
==================================================================

Ce script démontre le fonctionnement du système de vérification automatique
des documents avant qu'ils passent dans les formulaires.

Auteur: Assistant IA
Date: 2025
"""

import os
import sys
import tempfile
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_verification_service():
    """Test du service de vérification des documents."""
    print("🔍 TEST DU SYSTÈME DE VÉRIFICATION DE VÉRACITÉ DES DOCUMENTS")
    print("=" * 70)
    
    try:
        # Import du service de vérification
        from core.services.verification_documents import DocumentVerificationService
        
        # Créer une instance du service
        service = DocumentVerificationService()
        
        print("✅ Service de vérification créé avec succès")
        
        # Test 1: Vérification d'une pièce d'identité simulée
        print("\n📋 TEST 1: Vérification d'une pièce d'identité")
        print("-" * 50)
        
        # Créer un fichier temporaire simulé
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("RÉPUBLIQUE FRANÇAISE\nCARTE NATIONALE D'IDENTITÉ\nNOM: DUPONT\nPRÉNOM: JEAN")
            temp_file_path = temp_file.name
        
        try:
            # Vérifier le document
            result = service.verify_document(temp_file_path, 'piece_identite')
            
            print(f"   📄 Document: {os.path.basename(temp_file_path)}")
            print(f"   ✅ Valide: {result.is_valid}")
            print(f"   🎯 Score de confiance: {result.confidence_score:.2f}")
            print(f"   ⚠️  Avertissements: {len(result.warnings)}")
            print(f"   ❌ Erreurs: {len(result.errors)}")
            print(f"   🚨 Indicateurs de fraude: {len(result.fraud_indicators)}")
            
            if result.warnings:
                print("   📝 Avertissements:")
                for warning in result.warnings:
                    print(f"      - {warning}")
            
            if result.recommendations:
                print("   💡 Recommandations:")
                for rec in result.recommendations:
                    print(f"      - {rec}")
                    
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(temp_file_path)
        
        # Test 2: Vérification d'un justificatif de domicile
        print("\n🏠 TEST 2: Vérification d'un justificatif de domicile")
        print("-" * 50)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("EDF ÉLECTRICITÉ DE FRANCE\nFACTURE\nADRESSE: 123 RUE DE LA PAIX\nMONTANT: 45.67€")
            temp_file_path = temp_file.name
        
        try:
            result = service.verify_document(temp_file_path, 'justificatif_domicile')
            
            print(f"   📄 Document: {os.path.basename(temp_file_path)}")
            print(f"   ✅ Valide: {result.is_valid}")
            print(f"   🎯 Score de confiance: {result.confidence_score:.2f}")
            print(f"   ⚠️  Avertissements: {len(result.warnings)}")
            print(f"   ❌ Erreurs: {len(result.errors)}")
            print(f"   🚨 Indicateurs de fraude: {len(result.fraud_indicators)}")
            
        finally:
            os.unlink(temp_file_path)
        
        # Test 3: Vérification d'un document suspect
        print("\n🚨 TEST 3: Vérification d'un document suspect")
        print("-" * 50)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("DOCUMENT SUSPECT\n█▓▒░▄▌▐▀\nTEXTE RÉPÉTITIF TEXTE RÉPÉTITIF TEXTE RÉPÉTITIF")
            temp_file_path = temp_file.name
        
        try:
            result = service.verify_document(temp_file_path, 'piece_identite')
            
            print(f"   📄 Document: {os.path.basename(temp_file_path)}")
            print(f"   ✅ Valide: {result.is_valid}")
            print(f"   🎯 Score de confiance: {result.confidence_score:.2f}")
            print(f"   ⚠️  Avertissements: {len(result.warnings)}")
            print(f"   ❌ Erreurs: {len(result.errors)}")
            print(f"   🚨 Indicateurs de fraude: {len(result.fraud_indicators)}")
            
            if result.fraud_indicators:
                print("   🚨 Indicateurs de fraude détectés:")
                for indicator in result.fraud_indicators:
                    print(f"      - {indicator}")
            
        finally:
            os.unlink(temp_file_path)
        
        # Test 4: Statistiques de vérification
        print("\n📊 TEST 4: Statistiques de vérification")
        print("-" * 50)
        
        stats = service.get_statistics()
        if stats:
            print(f"   📈 Total des vérifications: {stats.get('total_verifications', 0)}")
            print(f"   ✅ Documents validés: {stats.get('valid_documents', 0)}")
            print(f"   ❌ Documents rejetés: {stats.get('invalid_documents', 0)}")
            print(f"   🎯 Taux de succès: {stats.get('success_rate', 0):.1f}%")
            print(f"   🎯 Score de confiance moyen: {stats.get('average_confidence', 0):.2f}")
            
            # Détails par type de document
            doc_types = stats.get('document_types', {})
            if doc_types:
                print("   📋 Répartition par type:")
                for doc_type, counts in doc_types.items():
                    print(f"      - {doc_type}: {counts['valid']}/{counts['total']} validés")
        else:
            print("   ℹ️  Aucune statistique disponible")
        
        print("\n✅ Tous les tests de vérification ont été exécutés avec succès !")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Assurez-vous que Django est configuré et que le service est accessible")
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()


def test_form_integration():
    """Test de l'intégration avec les formulaires Django."""
    print("\n🔧 TEST DE L'INTÉGRATION AVEC LES FORMULAIRES")
    print("=" * 70)
    
    try:
        # Simuler l'intégration avec un formulaire
        print("📝 Simulation de l'intégration avec un formulaire de locataire")
        
        # Créer un fichier temporaire pour la simulation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("RÉPUBLIQUE FRANÇAISE\nCARTE NATIONALE D'IDENTITÉ\nNOM: MARTIN\nPRÉNOM: MARIE")
            temp_file_path = temp_file.name
        
        try:
            # Simuler la vérification avant validation du formulaire
            from core.services.verification_documents import document_verification_service
            
            print("   🔍 Vérification automatique en cours...")
            result = document_verification_service.verify_document(temp_file_path, 'piece_identite')
            
            if result.is_valid:
                print("   ✅ Document validé - Le formulaire peut être soumis")
                print(f"   🎯 Score de confiance: {result.confidence_score:.2f}")
            else:
                print("   ❌ Document rejeté - Le formulaire sera bloqué")
                print("   🚨 Raisons du rejet:")
                for error in result.errors:
                    print(f"      - {error}")
                for indicator in result.fraud_indicators:
                    print(f"      - {indicator}")
            
            print("   💡 Recommandations:")
            for rec in result.recommendations:
                print(f"      - {rec}")
                
        finally:
            os.unlink(temp_file_path)
        
        print("\n✅ Test d'intégration réussi !")
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")


def test_middleware_simulation():
    """Simulation du fonctionnement du middleware."""
    print("\n🔄 SIMULATION DU MIDDLEWARE DE VÉRIFICATION")
    print("=" * 70)
    
    try:
        print("📤 Simulation d'un upload de fichier...")
        
        # Créer plusieurs fichiers temporaires pour la simulation
        files_to_upload = {
            'piece_identite': "RÉPUBLIQUE FRANÇAISE\nCARTE NATIONALE D'IDENTITÉ",
            'justificatif_domicile': "EDF ÉLECTRICITÉ DE FRANCE\nFACTURE",
            'attestation_bancaire': "BANQUE POPULAIRE\nRIB\nIBAN: FR123456789"
        }
        
        temp_files = {}
        
        try:
            # Créer les fichiers temporaires
            for field_name, content in files_to_upload.items():
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                temp_file.write(content)
                temp_file.close()
                temp_files[field_name] = temp_file.name
            
            print("   📁 Fichiers créés:")
            for field_name, file_path in temp_files.items():
                print(f"      - {field_name}: {os.path.basename(file_path)}")
            
            # Simuler la vérification par le middleware
            print("\n   🔍 Vérification automatique par le middleware...")
            
            from core.services.verification_documents import document_verification_service
            
            verification_results = {}
            files_to_reject = []
            
            for field_name, file_path in temp_files.items():
                # Déterminer le type de document
                document_type = field_name
                
                # Vérifier le document
                result = document_verification_service.verify_document(file_path, document_type)
                verification_results[field_name] = result
                
                # Marquer pour rejet si invalide
                if not result.is_valid:
                    files_to_reject.append(field_name)
            
            # Afficher les résultats
            print("\n   📊 Résultats de la vérification:")
            for field_name, result in verification_results.items():
                status = "✅ VALIDÉ" if result.is_valid else "❌ REJETÉ"
                print(f"      - {field_name}: {status} (Score: {result.confidence_score:.2f})")
            
            if files_to_reject:
                print(f"\n   🚨 Fichiers rejetés: {', '.join(files_to_reject)}")
                print("   ⚠️  Le formulaire sera bloqué jusqu'à correction")
            else:
                print("\n   ✅ Tous les documents sont valides")
                print("   🚀 Le formulaire peut être soumis")
            
            # Statistiques finales
            valid_count = sum(1 for result in verification_results.values() if result.is_valid)
            total_count = len(verification_results)
            
            print(f"\n   📈 Résumé: {valid_count}/{total_count} documents validés")
            
        finally:
            # Nettoyer les fichiers temporaires
            for file_path in temp_files.values():
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
        
        print("\n✅ Simulation du middleware réussie !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la simulation du middleware: {e}")


def main():
    """Fonction principale."""
    print("🚀 DÉMONSTRATION DU SYSTÈME DE VÉRIFICATION DE VÉRACITÉ")
    print("=" * 70)
    print("Ce script démontre comment le système vérifie automatiquement")
    print("la véracité des documents avant qu'ils passent dans les formulaires.")
    print()
    
    # Exécuter les tests
    test_verification_service()
    test_form_integration()
    test_middleware_simulation()
    
    print("\n" + "=" * 70)
    print("🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS !")
    print()
    print("📋 RÉSUMÉ DES FONCTIONNALITÉS:")
    print("   ✅ Vérification automatique des documents")
    print("   ✅ Détection de fraude et anomalies")
    print("   ✅ Intégration transparente avec les formulaires")
    print("   ✅ Blocage des documents suspects")
    print("   ✅ Feedback immédiat à l'utilisateur")
    print("   ✅ Historique et statistiques de vérification")
    print()
    print("🔧 POUR INTÉGRER DANS VOTRE APPLICATION:")
    print("   1. Ajouter le middleware dans settings.py")
    print("   2. Utiliser DocumentVerificationFormMixin dans vos formulaires")
    print("   3. Les vérifications se feront automatiquement")
    print()
    print("💡 AVANTAGES:")
    print("   - Sécurité renforcée")
    print("   - Conformité documentaire")
    print("   - Détection automatique des fraudes")
    print("   - Traçabilité complète")
    print("   - Interface utilisateur transparente")


if __name__ == "__main__":
    main()
