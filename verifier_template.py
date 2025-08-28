#!/usr/bin/env python
"""
Script pour vérifier exactement ce qui est affiché dans le template
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

def verifier_template():
    """Vérifier exactement ce qui est affiché dans le template"""
    
    print("🔍 VÉRIFICATION DU TEMPLATE DE VALIDATION")
    print("=" * 50)
    
    # Récupérer un utilisateur existant
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("❌ Aucun utilisateur trouvé dans la base")
            return False
        print(f"✅ Utilisateur: {user.username}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Récupérer un paiement en attente
    try:
        paiement = Paiement.objects.filter(statut='en_attente').first()
        if not paiement:
            print("❌ Aucun paiement en attente trouvé")
            return False
        print(f"✅ Paiement trouvé: {paiement.reference_paiement}")
        print(f"   Statut: {paiement.statut}")
        print(f"   ID: {paiement.pk}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Tester l'interface
    client = Client()
    client.force_login(user)
    
    print(f"\n🔍 TEST DE LA PAGE DE DÉTAIL")
    print("-" * 40)
    
    # Test de la page de détail
    try:
        response = client.get(f'/paiements/detail/{paiement.pk}/')
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            print(f"\n📋 CONTENU DE LA PAGE:")
            print("-" * 30)
            
            # Vérifier les éléments clés
            elements_a_verifier = [
                'Valider le Paiement',
                'Refuser le Paiement',
                'validerPaiement(',
                'refuserPaiement(',
                'Boutons d\'action',
                'action-buttons'
            ]
            
            for element in elements_a_verifier:
                if element in content:
                    print(f"   ✅ '{element}' TROUVÉ")
                else:
                    print(f"   ❌ '{element}' NON TROUVÉ")
            
            # Vérifier les permissions
            print(f"\n🔐 VÉRIFICATION DES PERMISSIONS:")
            print("-" * 30)
            
            user_groups = [group.name for group in user.groups.all()]
            print(f"   Groupes de l'utilisateur: {user_groups}")
            
            # Vérifier si l'utilisateur a les bonnes permissions
            if 'PRIVILEGE' in user_groups or 'ADMINISTRATION' in user_groups or 'COMPTABILITE' in user_groups:
                print("   ✅ Utilisateur a les bonnes permissions")
            else:
                print("   ❌ Utilisateur n'a PAS les bonnes permissions")
            
            # Vérifier le statut du paiement
            print(f"\n📊 STATUT DU PAIEMENT:")
            print("-" * 30)
            print(f"   Statut actuel: {paiement.statut}")
            print(f"   Peut être validé: {paiement.statut == 'en_attente'}")
            
            # Extraire la section des boutons d'action
            if 'Boutons d\'action' in content:
                start = content.find('Boutons d\'action')
                end = content.find('</div>', start) + 6
                section_boutons = content[start:end]
                print(f"\n🔘 SECTION BOUTONS D'ACTION:")
                print("-" * 30)
                print(section_boutons[:500] + "..." if len(section_boutons) > 500 else section_boutons)
            else:
                print(f"\n❌ SECTION 'Boutons d\'action' NON TROUVÉE")
                
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {e}")
    
    return True

if __name__ == '__main__':
    verifier_template()
