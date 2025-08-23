#!/usr/bin/env python
"""
Script pour tester la distribution des pages par groupe
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from django.test import Client
from django.contrib.auth import authenticate

def test_distribution_pages_groupes():
    """Test de la distribution des pages par groupe"""
    
    print("🧪 TEST DE LA DISTRIBUTION DES PAGES PAR GROUPE")
    print("=" * 60)
    
    # Récupérer tous les groupes
    groupes = GroupeTravail.objects.all()
    
    for groupe in groupes:
        print(f"\n📋 GROUPE: {groupe.nom}")
        print("-" * 40)
        
        # Afficher les permissions du groupe
        permissions = groupe.permissions
        print(f"📝 Description: {groupe.description}")
        print(f"🔑 Modules accessibles: {', '.join(permissions.get('modules', []))}")
        print(f"⚡ Actions autorisées: {', '.join(permissions.get('actions', []))}")
        print(f"🚫 Restrictions: {', '.join(permissions.get('restrictions', []))}")
        
        # Trouver un utilisateur de test pour ce groupe
        utilisateur_test = Utilisateur.objects.filter(
            groupe_travail=groupe,
            actif=True
        ).first()
        
        if utilisateur_test:
            print(f"👤 Utilisateur de test: {utilisateur_test.username}")
            
            # Tester l'accès au dashboard
            client = Client()
            if client.login(username=utilisateur_test.username, password='test123'):
                print("✅ Connexion réussie")
                
                # Tester l'accès au dashboard du groupe
                response = client.get(f'/utilisateurs/dashboard/{groupe.nom}/')
                if response.status_code == 200:
                    print(f"✅ Dashboard {groupe.nom} accessible")
                else:
                    print(f"❌ Dashboard {groupe.nom} non accessible (code: {response.status_code})")
            else:
                print("❌ Échec de la connexion")
        else:
            print("❌ Aucun utilisateur de test trouvé pour ce groupe")
    
    print("\n🎯 DISTRIBUTION DES PAGES PAR FONCTION:")
    print("=" * 60)
    
    print("\n📊 CAISSE:")
    print("   • Paiements (création, validation, suivi)")
    print("   • Retraits vers les bailleurs")
    print("   • Suivi des cautions")
    print("   • Rapports financiers")
    print("   • Template: dashboard_caisse.html")
    
    print("\n📋 ADMINISTRATION:")
    print("   • Propriétés (création, modification, suivi)")
    print("   • Bailleurs (gestion complète)")
    print("   • Locataires (gestion complète)")
    print("   • Contrats (création, modification, renouvellement)")
    print("   • Notifications")
    print("   • Template: dashboard_administration.html")
    
    print("\n🔍 CONTROLES:")
    print("   • Contrôle des paiements")
    print("   • Validation des contrats")
    print("   • Audit des données")
    print("   • Rapports de contrôle")
    print("   • Template: dashboard_controles.html")
    
    print("\n👑 PRIVILEGE:")
    print("   • Toutes les pages")
    print("   • Gestion des utilisateurs")
    print("   • Gestion des groupes")
    print("   • Configuration système")
    print("   • Template: dashboard_privilege.html")
    
    print("\n✅ Test de distribution terminé!")

if __name__ == '__main__':
    test_distribution_pages_groupes() 