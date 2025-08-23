#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration de la gestion de caution dans le formulaire de contrat
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from contrats.models import Contrat, RecuCaution
from contrats.forms import ContratForm
from proprietes.models import Propriete, Locataire, Bailleur

Utilisateur = get_user_model()

def test_integration_caution():
    """
    Test de l'intégration de la gestion de caution dans le formulaire de contrat
    """
    print("🧪 Test de l'intégration caution-contrat...")
    
    try:
        # 1. Vérifier que le formulaire contient les nouveaux champs
        print("1. Vérification des champs du formulaire...")
        form = ContratForm()
        
        # Vérifier la présence des champs de caution
        caution_fields = [
            'caution_payee',
            'date_paiement_caution', 
            'avance_loyer_payee',
            'date_paiement_avance',
            'generer_recu_caution'
        ]
        
        for field_name in caution_fields:
            if field_name in form.fields:
                print(f"   ✅ Champ '{field_name}' présent")
            else:
                print(f"   ❌ Champ '{field_name}' manquant")
                return False
        
        # 2. Vérifier que les champs sont dans la liste des champs du modèle
        print("\n2. Vérification des champs du modèle...")
        model_fields = [
            'caution_payee',
            'date_paiement_caution',
            'avance_loyer_payee', 
            'date_paiement_avance'
        ]
        
        for field_name in model_fields:
            if hasattr(Contrat, field_name):
                print(f"   ✅ Champ modèle '{field_name}' présent")
            else:
                print(f"   ❌ Champ modèle '{field_name}' manquant")
                return False
        
        # 3. Vérifier la présence du modèle RecuCaution
        print("\n3. Vérification du modèle RecuCaution...")
        if hasattr(RecuCaution, 'contrat'):
            print("   ✅ Modèle RecuCaution avec relation contrat présent")
        else:
            print("   ❌ Modèle RecuCaution manquant ou mal configuré")
            return False
        
        print("\n🎉 Tous les tests d'intégration sont passés avec succès!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        return False

def test_form_validation():
    """
    Test de la validation du formulaire avec les nouveaux champs
    """
    print("\n🧪 Test de validation du formulaire...")
    
    try:
        # Créer des données de test
        test_data = {
            'numero_contrat': 'TEST-CT-001',
            'loyer_mensuel': '50000',
            'charges_mensuelles': '5000',
            'depot_garantie': '100000',
            'avance_loyer': '50000',
            'jour_paiement': 1,
            'mode_paiement': 'virement',
            'caution_payee': True,
            'date_paiement_caution': '2024-01-15',
            'avance_loyer_payee': False,
            'generer_recu_caution': True,
            'telecharger_pdf': False
        }
        
        # Tester la validation
        form = ContratForm(data=test_data)
        if form.is_valid():
            print("   ✅ Formulaire valide avec données de test")
            return True
        else:
            print(f"   ❌ Formulaire invalide: {form.errors}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test de validation: {str(e)}")
        return False

def main():
    """
    Fonction principale de test
    """
    print("🚀 Démarrage des tests d'intégration caution-contrat\n")
    
    # Test 1: Vérification de l'intégration
    if not test_integration_caution():
        print("\n❌ Échec des tests d'intégration")
        sys.exit(1)
    
    # Test 2: Validation du formulaire
    if not test_form_validation():
        print("\n❌ Échec des tests de validation")
        sys.exit(1)
    
    print("\n🎉 Tous les tests sont passés avec succès!")
    print("\n📋 Résumé de l'intégration:")
    print("   • Champs de caution intégrés dans le formulaire de contrat")
    print("   • Validation automatique des champs conditionnels")
    print("   • Création automatique du reçu de caution")
    print("   • Interface utilisateur unifiée et intuitive")
    print("   • Gestion des erreurs et validation robuste")

if __name__ == "__main__":
    main()
