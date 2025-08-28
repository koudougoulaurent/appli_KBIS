#!/usr/bin/env python
"""
Test simple de validation des paiements
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from paiements.models import Paiement

def test_validation_simple():
    """Test simple de validation"""
    
    print("🧪 TEST SIMPLE DE VALIDATION")
    print("=" * 40)
    
    # Récupérer un utilisateur
    User = get_user_model()
    user = User.objects.first()
    print(f"✅ Utilisateur: {user.username}")
    
    # Récupérer un paiement en attente
    paiement = Paiement.objects.filter(statut='en_attente').first()
    if not paiement:
        print("❌ Aucun paiement en attente trouvé")
        return False
    
    print(f"✅ Paiement trouvé: {paiement.reference_paiement}")
    print(f"   ID: {paiement.pk}")
    print(f"   Statut: {paiement.statut}")
    
    # Tester directement la validation
    client = Client()
    client.force_login(user)
    
    print(f"\n🔍 TEST DE VALIDATION DIRECTE")
    print("-" * 30)
    
    # Test de l'URL de validation
    validation_url = f'/paiements/paiement/{paiement.pk}/valider/'
    print(f"   URL testée: {validation_url}")
    
    try:
        response = client.post(validation_url)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Validation réussie !")
            # Vérifier que le paiement a été mis à jour
            paiement.refresh_from_db()
            print(f"   Nouveau statut: {paiement.statut}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Contenu: {response.content}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    return True

if __name__ == '__main__':
    test_validation_simple()
