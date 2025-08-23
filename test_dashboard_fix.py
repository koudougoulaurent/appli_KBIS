#!/usr/bin/env python
"""
Script de test pour vérifier que le dashboard ADMINISTRATION fonctionne
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from utilisateurs.models import Utilisateur, GroupeTravail

def test_dashboard_administration():
    """Test du dashboard ADMINISTRATION"""
    print("🧪 Test du dashboard ADMINISTRATION...")
    
    # Créer un client de test
    client = Client()
    
    # Créer un utilisateur ADMINISTRATION pour le test
    groupe_admin, created = GroupeTravail.objects.get_or_create(
        nom='ADMINISTRATION',
        defaults={
            'description': 'Groupe administration',
            'permissions': {'modules': ['all']},
            'actif': True
        }
    )
    
    admin_user, created = Utilisateur.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'test_admin@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Admin',
            'is_active': True,
            'is_staff': True,
            'groupe_travail': groupe_admin
        }
    )
    
    # Connecter l'utilisateur
    client.force_login(admin_user)
    
    # Tester l'accès au dashboard ADMINISTRATION
    try:
        response = client.get(reverse('utilisateurs:dashboard_groupe', kwargs={'groupe_nom': 'ADMINISTRATION'}))
        print(f"✅ Dashboard ADMINISTRATION: {response.status_code} (attendu: 200)")
        
        if response.status_code == 200:
            print("✅ Le dashboard ADMINISTRATION fonctionne correctement !")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    print("\n✅ Test terminé !")

if __name__ == '__main__':
    test_dashboard_administration() 