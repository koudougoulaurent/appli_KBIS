#!/usr/bin/env python
"""
Script de test pour le système de validation des paiements
"""

import os
import sys
import django
import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from paiements.models import Paiement, Contrat
from proprietes.models import Propriete, Locataire, Bailleur
from core.models import Devise

def test_systeme_validation():
    """Test du système de validation des paiements"""
    
    print("🧪 TEST DU SYSTÈME DE VALIDATION DES PAIEMENTS")
    print("=" * 50)
    
    # Récupérer un utilisateur existant
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé dans la base")
            return False
        print(f"✅ Utilisateur de test: {user.username}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'utilisateur: {e}")
        return False
    
    # Récupérer un contrat existant
    try:
        contrat = Contrat.objects.filter(is_deleted=False).first()
        if not contrat:
            print("❌ Aucun contrat trouvé dans la base")
            return False
        print(f"✅ Contrat de test: {contrat.numero_contrat}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du contrat: {e}")
        return False
    
    # Récupérer la devise de base
    try:
        devise = Devise.objects.filter(is_devise_base=True).first()
        if not devise:
            print("⚠️ Aucune devise de base trouvée")
        else:
            print(f"✅ Devise de base: {devise.code}")
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération de la devise: {e}")
    
    # Créer un paiement de test
    try:
        paiement = Paiement.objects.create(
            contrat=contrat,
            montant=50000,
            type_paiement='loyer',
            mode_paiement='virement',
            date_paiement='2025-01-15',
            statut='en_attente',
            cree_par=user,
            reference_paiement=f'TEST-{user.username}-{int(time.time())}-001'
        )
        print(f"✅ Paiement de test créé: {paiement.reference_paiement}")
        print(f"   Statut initial: {paiement.statut}")
        print(f"   Montant: {paiement.montant} F CFA")
    except Exception as e:
        print(f"❌ Erreur lors de la création du paiement de test: {e}")
        return False
    
    # Tester la validation via l'API
    client = Client()
    client.force_login(user)
    
    print("\n🔍 TEST DE VALIDATION VIA L'API")
    print("-" * 30)
    
    # Test de validation
    try:
        response = client.post(f'/paiements/paiement/{paiement.pk}/valider/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Validation réussie: {data.get('message')}")
                print(f"   Nouveau statut: {data.get('statut')}")
                print(f"   Quittance générée: {data.get('quittance_generee')}")
                
                # Vérifier que le paiement a été mis à jour
                paiement.refresh_from_db()
                print(f"   Statut en base: {paiement.statut}")
                print(f"   Validé par: {paiement.valide_par}")
                print(f"   Date d'encaissement: {paiement.date_encaissement}")
                
            else:
                print(f"   ❌ Erreur de validation: {data.get('error')}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Contenu: {response.content}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test de validation: {e}")
    
    # Test de refus
    print("\n🔍 TEST DE REFUS VIA L'API")
    print("-" * 30)
    
    # Créer un autre paiement pour le test de refus
    try:
        paiement_refus = Paiement.objects.create(
            contrat=contrat,
            montant=30000,
            type_paiement='charges',
            mode_paiement='cheque',
            date_paiement='2025-01-16',
            statut='en_attente',
            cree_par=user,
            reference_paiement=f'TEST-{user.username}-{int(time.time())}-002'
        )
        print(f"   Paiement de test pour refus créé: {paiement_refus.reference_paiement}")
        
        response = client.post(f'/paiements/paiement/{paiement_refus.pk}/refuser/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Refus réussi: {data.get('message')}")
                print(f"   Nouveau statut: {data.get('statut')}")
                
                # Vérifier que le paiement a été mis à jour
                paiement_refus.refresh_from_db()
                print(f"   Statut en base: {paiement_refus.statut}")
                
            else:
                print(f"   ❌ Erreur de refus: {data.get('error')}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test de refus: {e}")
    
    # Nettoyage
    print("\n🧹 NETTOYAGE")
    print("-" * 30)
    
    try:
        paiement.delete()
        paiement_refus.delete()
        print("✅ Paiements de test supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 TEST TERMINÉ")
    
    return True

if __name__ == '__main__':
    test_systeme_validation()
