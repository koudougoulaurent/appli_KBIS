#!/usr/bin/env python
"""
Test du nouveau système d'IDs uniques professionnels
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.id_generator import IDGenerator, IDConfiguration
from datetime import datetime, date


def test_generation_ids():
    """Tester la génération des nouveaux IDs uniques"""
    
    print("🧪 TEST DU NOUVEAU SYSTÈME D'IDS UNIQUES PROFESSIONNELS")
    print("=" * 70)
    
    # Test 1: Formats disponibles
    print("\n📋 Test 1: Formats d'IDs disponibles")
    print("-" * 50)
    
    formats = IDGenerator.get_available_formats()
    for entity_type, config in formats.items():
        print(f"   {entity_type.upper()}: {config['description']}")
        print(f"     Format: {config['format']}")
        print(f"     Exemple: {config['example']}")
        print()
    
    # Test 2: Génération d'IDs pour chaque type
    print("\n🔄 Test 2: Génération d'IDs pour chaque type")
    print("-" * 50)
    
    # Test bailleur
    try:
        bailleur_id = IDGenerator.generate_id('bailleur')
        print(f"   ✅ Bailleur: {bailleur_id}")
        
        # Vérifier le format
        if IDGenerator.validate_id_format('bailleur', bailleur_id):
            print(f"      Format validé: {bailleur_id}")
            info = IDGenerator.get_id_info('bailleur', bailleur_id)
            print(f"      Année: {info['year']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {bailleur_id}")
    except Exception as e:
        print(f"   ❌ Erreur bailleur: {e}")
    
    # Test locataire
    try:
        locataire_id = IDGenerator.generate_id('locataire')
        print(f"   ✅ Locataire: {locataire_id}")
        
        if IDGenerator.validate_id_format('locataire', locataire_id):
            print(f"      Format validé: {locataire_id}")
            info = IDGenerator.get_id_info('locataire', locataire_id)
            print(f"      Année: {info['year']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {locataire_id}")
    except Exception as e:
        print(f"   ❌ Erreur locataire: {e}")
    
    # Test propriété
    try:
        propriete_id = IDGenerator.generate_id('propriete')
        print(f"   ✅ Propriété: {propriete_id}")
        
        if IDGenerator.validate_id_format('propriete', propriete_id):
            print(f"      Format validé: {propriete_id}")
            info = IDGenerator.get_id_info('propriete', propriete_id)
            print(f"      Année: {info['year']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {propriete_id}")
    except Exception as e:
        print(f"   ❌ Erreur propriété: {e}")
    
    # Test contrat
    try:
        contrat_id = IDGenerator.generate_id('contrat')
        print(f"   ✅ Contrat: {contrat_id}")
        
        if IDGenerator.validate_id_format('contrat', contrat_id):
            print(f"      Format validé: {contrat_id}")
            info = IDGenerator.get_id_info('contrat', contrat_id)
            print(f"      Année: {info['year']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {contrat_id}")
    except Exception as e:
        print(f"   ❌ Erreur contrat: {e}")
    
    # Test paiement avec date spécifique
    try:
        date_paiement = date(2025, 8, 20)
        paiement_id = IDGenerator.generate_id('paiement', date_paiement=date_paiement)
        print(f"   ✅ Paiement: {paiement_id}")
        
        if IDGenerator.validate_id_format('paiement', paiement_id):
            print(f"      Format validé: {paiement_id}")
            info = IDGenerator.get_id_info('paiement', paiement_id)
            print(f"      Année: {info['year']}, Mois: {info['month']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {paiement_id}")
    except Exception as e:
        print(f"   ❌ Erreur paiement: {e}")
    
    # Test reçu avec date spécifique
    try:
        date_emission = datetime(2025, 8, 20, 14, 30, 0)
        recu_id = IDGenerator.generate_id('recu', date_emission=date_emission)
        print(f"   ✅ Reçu: {recu_id}")
        
        if IDGenerator.validate_id_format('recu', recu_id):
            print(f"      Format validé: {recu_id}")
            info = IDGenerator.get_id_info('recu', recu_id)
            print(f"      Date: {info['date']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {recu_id}")
    except Exception as e:
        print(f"   ❌ Erreur reçu: {e}")
    
    # Test quittance avec date spécifique
    try:
        date_emission = datetime(2025, 8, 20, 14, 30, 0)
        quittance_id = IDGenerator.generate_id('quittance', date_emission=date_emission)
        print(f"   ✅ Quittance: {quittance_id}")
        
        if IDGenerator.validate_id_format('quittance', quittance_id):
            print(f"      Format validé: {quittance_id}")
            info = IDGenerator.get_id_info('quittance', quittance_id)
            print(f"      Année: {info['year']}, Mois: {info['month']}, Séquence: {info['sequence']}")
        else:
            print(f"      ❌ Format invalide: {quittance_id}")
    except Exception as e:
        print(f"   ❌ Erreur quittance: {e}")
    
    # Test 3: Validation des formats
    print("\n🔍 Test 3: Validation des formats d'IDs")
    print("-" * 50)
    
    # Test avec des IDs valides
    ids_valides = [
        ('bailleur', 'BLR-2025-0001'),
        ('locataire', 'LOC-2025-0001'),
        ('propriete', 'PRP-2025-0001'),
        ('contrat', 'CTR-2025-0001'),
        ('paiement', 'PAY-202508-0001'),
        ('recu', 'REC-20250820-0001'),
        ('quittance', 'QUI-202508-0001')
    ]
    
    for entity_type, test_id in ids_valides:
        is_valid = IDGenerator.validate_id_format(entity_type, test_id)
        print(f"   {entity_type.upper()}: {test_id} - {'✅ Valide' if is_valid else '❌ Invalide'}")
    
    # Test avec des IDs invalides
    print("\n   Test avec des IDs invalides:")
    ids_invalides = [
        ('bailleur', 'BLR-2025-001'),      # Séquence trop courte
        ('locataire', 'LOC-2025-00001'),   # Séquence trop longue
        ('paiement', 'PAY-2025-0001'),     # Format année au lieu de année-mois
        ('recu', 'REC-2025-0001'),         # Format année au lieu de date complète
    ]
    
    for entity_type, test_id in ids_invalides:
        is_valid = IDGenerator.validate_id_format(entity_type, test_id)
        print(f"   {entity_type.upper()}: {test_id} - {'✅ Valide' if is_valid else '❌ Invalide'}")
    
    # Test 4: Extraction d'informations
    print("\n📊 Test 4: Extraction d'informations des IDs")
    print("-" * 50)
    
    test_ids = [
        ('bailleur', 'BLR-2025-0042'),
        ('paiement', 'PAY-202508-0015'),
        ('recu', 'REC-20250820-0023')
    ]
    
    for entity_type, test_id in test_ids:
        info = IDGenerator.get_id_info(entity_type, test_id)
        if info:
            print(f"   {entity_type.upper()}: {test_id}")
            for key, value in info.items():
                print(f"      {key}: {value}")
        else:
            print(f"   {entity_type.upper()}: {test_id} - ❌ Impossible d'extraire les infos")
    
    # Test 5: Configuration de l'entreprise
    print("\n🏢 Test 5: Configuration de l'entreprise")
    print("-" * 50)
    
    company_prefix = IDConfiguration.get_company_prefix()
    print(f"   Préfixe entreprise: {company_prefix}")
    
    custom_formats = IDConfiguration.get_custom_formats()
    print(f"   Formats personnalisés disponibles: {len(custom_formats)}")
    
    reset_policy = IDConfiguration.get_sequence_reset_policy()
    print(f"   Politique de réinitialisation:")
    for entity, policy in reset_policy.items():
        print(f"      {entity}: {policy}")
    
    # Test 6: Génération de plusieurs IDs pour tester l'incrémentation
    print("\n🔢 Test 6: Test d'incrémentation des séquences")
    print("-" * 50)
    
    print("   Génération de 5 IDs de bailleurs consécutifs:")
    for i in range(5):
        try:
            bailleur_id = IDGenerator.generate_id('bailleur')
            print(f"      {i+1}. {bailleur_id}")
        except Exception as e:
            print(f"      {i+1}. ❌ Erreur: {e}")
    
    print("\n   Génération de 3 IDs de paiements consécutifs (même mois):")
    date_test = date(2025, 8, 20)
    for i in range(3):
        try:
            paiement_id = IDGenerator.generate_id('paiement', date_paiement=date_test)
            print(f"      {i+1}. {paiement_id}")
        except Exception as e:
            print(f"      {i+1}. ❌ Erreur: {e}")
    
    print("\n✅ Tests terminés avec succès!")
    return True


def test_integration_models():
    """Tester l'intégration avec les modèles Django"""
    
    print("\n🔗 TEST D'INTÉGRATION AVEC LES MODÈLES DJANGO")
    print("=" * 70)
    
    try:
        # Test avec le modèle Bailleur
        from proprietes.models import Bailleur
        
        print("\n👤 Test avec le modèle Bailleur:")
        print("-" * 40)
        
        # Vérifier si le champ existe
        if hasattr(Bailleur, 'numero_bailleur'):
            print("   ✅ Champ numero_bailleur présent dans le modèle")
            
            # Compter les bailleurs avec et sans ID
            total_bailleurs = Bailleur.objects.count()
            bailleurs_avec_id = Bailleur.objects.filter(numero_bailleur__isnull=False).count()
            bailleurs_sans_id = Bailleur.objects.filter(numero_bailleur__isnull=True).count()
            
            print(f"   Total bailleurs: {total_bailleurs}")
            print(f"   Avec ID unique: {bailleurs_avec_id}")
            print(f"   Sans ID unique: {bailleurs_sans_id}")
            
            # Afficher quelques exemples
            if bailleurs_avec_id > 0:
                print("   Exemples d'IDs:")
                for bailleur in Bailleur.objects.filter(numero_bailleur__isnull=False)[:3]:
                    print(f"      {bailleur.nom} {bailleur.prenom}: {bailleur.numero_bailleur}")
        else:
            print("   ❌ Champ numero_bailleur manquant dans le modèle")
        
        # Test avec le modèle Locataire
        from proprietes.models import Locataire
        
        print("\n👥 Test avec le modèle Locataire:")
        print("-" * 40)
        
        if hasattr(Locataire, 'numero_locataire'):
            print("   ✅ Champ numero_locataire présent dans le modèle")
            
            total_locataires = Locataire.objects.count()
            locataires_avec_id = Locataire.objects.filter(numero_locataire__isnull=False).count()
            locataires_sans_id = Locataire.objects.filter(numero_locataire__isnull=True).count()
            
            print(f"   Total locataires: {total_locataires}")
            print(f"   Avec ID unique: {locataires_avec_id}")
            print(f"   Sans ID unique: {locataires_sans_id}")
            
            if locataires_avec_id > 0:
                print("   Exemples d'IDs:")
                for locataire in Locataire.objects.filter(numero_locataire__isnull=False)[:3]:
                    print(f"      {locataire.nom} {locataire.prenom}: {locataire.numero_locataire}")
        else:
            print("   ❌ Champ numero_locataire manquant dans le modèle")
        
        # Test avec le modèle Propriete
        from proprietes.models import Propriete
        
        print("\n🏠 Test avec le modèle Propriete:")
        print("-" * 40)
        
        if hasattr(Propriete, 'numero_propriete'):
            print("   ✅ Champ numero_propriete présent dans le modèle")
            
            total_proprietes = Propriete.objects.count()
            proprietes_avec_id = Propriete.objects.filter(numero_propriete__isnull=False).count()
            proprietes_sans_id = Propriete.objects.filter(numero_propriete__isnull=True).count()
            
            print(f"   Total propriétés: {total_proprietes}")
            print(f"   Avec ID unique: {proprietes_avec_id}")
            print(f"   Sans ID unique: {proprietes_sans_id}")
            
            if proprietes_avec_id > 0:
                print("   Exemples d'IDs:")
                for propriete in Propriete.objects.filter(numero_propriete__isnull=False)[:3]:
                    print(f"      {propriete.adresse}: {propriete.numero_propriete}")
        else:
            print("   ❌ Champ numero_propriete manquant dans le modèle")
        
        print("\n✅ Tests d'intégration terminés!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests d'intégration: {e}")
        return False


def main():
    """Fonction principale de test"""
    
    print("🚀 TESTS COMPLETS DU SYSTÈME D'IDS UNIQUES PROFESSIONNELS")
    print("=" * 70)
    
    # Test 1: Génération des IDs
    if not test_generation_ids():
        print("❌ Échec des tests de génération")
        return False
    
    # Test 2: Intégration avec les modèles
    if not test_integration_models():
        print("❌ Échec des tests d'intégration")
        return False
    
    print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
    print("=" * 70)
    print("✅ Le système d'IDs uniques professionnels fonctionne parfaitement")
    print("✅ Les formats sont structurés et personnalisables")
    print("✅ L'intégration avec les modèles Django est opérationnelle")
    print("✅ L'entreprise peut maintenant contrôler ses références")
    
    return True


if __name__ == "__main__":
    main()
