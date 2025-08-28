#!/usr/bin/env python
"""
Script de test pour l'interface de validation des paiements
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from paiements.models import Paiement, Contrat
from django.urls import reverse

def test_interface_validation():
    """Test de l'interface de validation des paiements"""
    
    print("🧪 TEST DE L'INTERFACE DE VALIDATION DES PAIEMENTS")
    print("=" * 60)
    
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
    
    # Créer un paiement de test
    try:
        import time
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
        print(f"   ID: {paiement.pk}")
    except Exception as e:
        print(f"❌ Erreur lors de la création du paiement de test: {e}")
        return False
    
    # Tester l'interface
    client = Client()
    client.force_login(user)
    
    print("\n🔍 TEST DE L'INTERFACE UTILISATEUR")
    print("-" * 40)
    
    # Test 1: Page de détail du paiement
    try:
        print("   📄 Test de la page de détail...")
        response = client.get(f'/paiements/detail/{paiement.pk}/')
        print(f"      Status code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Vérifier que les boutons de validation sont présents
            if 'Valider le Paiement' in content:
                print("      ✅ Bouton 'Valider le Paiement' trouvé")
            else:
                print("      ❌ Bouton 'Valider le Paiement' NON trouvé")
            
            if 'Refuser le Paiement' in content:
                print("      ✅ Bouton 'Refuser le Paiement' trouvé")
            else:
                print("      ❌ Bouton 'Refuser le Paiement' NON trouvé")
            
            # Vérifier que le JavaScript est présent
            if 'validerPaiement(' in content:
                print("      ✅ Fonction JavaScript 'validerPaiement' trouvée")
            else:
                print("      ❌ Fonction JavaScript 'validerPaiement' NON trouvée")
            
            if 'refuserPaiement(' in content:
                print("      ✅ Fonction JavaScript 'refuserPaiement' trouvée")
            else:
                print("      ❌ Fonction JavaScript 'refuserPaiement' NON trouvée")
            
        else:
            print(f"      ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Erreur lors du test de la page de détail: {e}")
    
    # Test 2: URLs de validation
    print("\n   🔗 Test des URLs de validation...")
    
    # Test de l'URL de validation
    try:
        validation_url = f'/paiements/paiement/{paiement.pk}/valider/'
        print(f"      URL de validation: {validation_url}")
        
        response = client.post(validation_url)
        print(f"      Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("      ✅ Validation réussie via l'URL")
                print(f"         Message: {data.get('message')}")
                
                # Vérifier que le paiement a été mis à jour
                paiement.refresh_from_db()
                print(f"         Nouveau statut: {paiement.statut}")
                
            else:
                print(f"      ❌ Erreur de validation: {data.get('error')}")
        else:
            print(f"      ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Erreur lors du test de l'URL de validation: {e}")
    
    # Test 3: Vérifier que la page de détail se recharge correctement
    print("\n   🔄 Test de rechargement de la page...")
    try:
        response = client.get(f'/paiements/detail/{paiement.pk}/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            if 'Paiement Validé' in content:
                print("      ✅ Badge 'Paiement Validé' trouvé après validation")
            else:
                print("      ❌ Badge 'Paiement Validé' NON trouvé après validation")
                
        else:
            print(f"      ❌ Erreur lors du rechargement: {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Erreur lors du test de rechargement: {e}")
    
    # Nettoyage
    print("\n🧹 NETTOYAGE")
    print("-" * 30)
    
    try:
        paiement.delete()
        print("✅ Paiement de test supprimé")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 TEST DE L'INTERFACE TERMINÉ")
    
    return True

if __name__ == '__main__':
    test_interface_validation()
