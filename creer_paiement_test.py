#!/usr/bin/env python
"""
Script pour créer un paiement de test visible dans l'interface
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from paiements.models import Paiement, Contrat
import time

def creer_paiement_test():
    """Créer un paiement de test visible dans l'interface"""
    
    print("🎯 CRÉATION D'UN PAIEMENT DE TEST VISIBLE")
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
    
    # Récupérer un contrat existant
    try:
        contrat = Contrat.objects.filter(is_deleted=False).first()
        if not contrat:
            print("❌ Aucun contrat trouvé dans la base")
            return False
        print(f"✅ Contrat: {contrat.numero_contrat}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Créer un paiement de test
    try:
        timestamp = int(time.time())
        paiement = Paiement.objects.create(
            contrat=contrat,
            montant=75000,
            type_paiement='loyer',
            mode_paiement='virement',
            date_paiement='2025-01-20',
            statut='en_attente',
            cree_par=user,
            reference_paiement=f'PAIEMENT-TEST-{timestamp}',
            notes='Paiement de test pour validation - Créé automatiquement'
        )
        
        print(f"✅ Paiement de test créé avec succès !")
        print(f"   Référence: {paiement.reference_paiement}")
        print(f"   ID: {paiement.pk}")
        print(f"   Statut: {paiement.statut}")
        print(f"   Montant: {paiement.montant} F CFA")
        print(f"   Contrat: {contrat.numero_contrat}")
        print(f"   Locataire: {contrat.locataire.get_nom_complet()}")
        print(f"   Propriété: {contrat.propriete.adresse}")
        
        print(f"\n🔗 LIENS DE TEST:")
        print(f"   Liste des paiements: http://127.0.0.1:8000/paiements/liste/")
        print(f"   Détail du paiement: http://127.0.0.1:8000/paiements/detail/{paiement.pk}/")
        print(f"   Détail alternatif: http://127.0.0.1:8000/paiements/paiement_detail/{paiement.pk}/")
        
        print(f"\n💡 INSTRUCTIONS:")
        print(f"   1. Allez sur la liste des paiements")
        print(f"   2. Trouvez le paiement '{paiement.reference_paiement}'")
        print(f"   3. Cliquez dessus pour voir les boutons de validation")
        print(f"   4. Vous devriez voir les boutons 'Valider' et 'Refuser'")
        
        return paiement
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False

if __name__ == '__main__':
    creer_paiement_test()
