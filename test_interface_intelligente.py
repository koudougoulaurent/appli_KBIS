#!/usr/bin/env python
"""
Test de l'interface intelligente d'ajout de paiement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_interface_intelligente():
    """Test de l'interface intelligente d'ajout de paiement"""
    
    print("🧪 TEST DE L'INTERFACE INTELLIGENTE")
    print("=" * 50)
    
    # Récupérer un utilisateur
    User = get_user_model()
    user = User.objects.first()
    print(f"✅ Utilisateur: {user.username}")
    
    # Tester l'interface
    client = Client()
    client.force_login(user)
    
    print(f"\n🔍 TEST DE LA PAGE D'AJOUT")
    print("-" * 40)
    
    # Test de la page d'ajout
    try:
        response = client.get('/paiements/ajouter/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            print(f"\n📋 ÉLÉMENTS VÉRIFIÉS:")
            print("-" * 30)
            
            # Vérifier les éléments clés de l'interface intelligente
            elements_a_verifier = [
                'Contexte Intelligent du Contrat',
                'Recherche Rapide de Contrat',
                'panneau-contexte',
                'contexte-intelligent',
                'Temps Réel',
                'Sélectionnez un contrat',
                'Historique des Paiements',
                'Suggestions de Paiement'
            ]
            
            for element in elements_a_verifier:
                if element in content:
                    print(f"   ✅ '{element}' TROUVÉ")
                else:
                    print(f"   ❌ '{element}' NON TROUVÉ")
            
            # Vérifier que le JavaScript est présent
            print(f"\n🔧 JAVASCRIPT:")
            print("-" * 30)
            
            if 'jquery' in content.lower():
                print("   ✅ jQuery trouvé")
            else:
                print("   ❌ jQuery NON trouvé")
            
            if 'select2' in content.lower():
                print("   ✅ Select2 trouvé")
            else:
                print("   ❌ Select2 NON trouvé")
            
            # Vérifier les URLs de l'API
            print(f"\n🔗 URLs DE L'API:")
            print("-" * 30)
            
            if '/paiements/api/recherche-rapide/' in content:
                print("   ✅ URL API recherche rapide trouvée")
            else:
                print("   ❌ URL API recherche rapide NON trouvée")
                
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")
    
    return True

if __name__ == '__main__':
    test_interface_intelligente()
