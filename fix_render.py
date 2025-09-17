#!/usr/bin/env python
"""
Script pour corriger le problème sur Render
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail

User = get_user_model()

def fix_render():
    """Corriger le problème sur Render"""
    print("🔧 Correction du problème sur Render...")
    
    # Créer les GroupeTravail s'ils n'existent pas
    groupes_data = [
        {
            'nom': 'PRIVILEGE',
            'description': 'Groupe avec tous les privilèges',
            'permissions': {
                'modules': ['all'],
                'actions': ['create', 'read', 'update', 'delete']
            }
        },
        {
            'nom': 'ADMINISTRATION',
            'description': 'Groupe d\'administration',
            'permissions': {
                'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'],
                'actions': ['create', 'read', 'update']
            }
        },
        {
            'nom': 'CAISSE',
            'description': 'Groupe de gestion de la caisse',
            'permissions': {
                'modules': ['paiements', 'contrats'],
                'actions': ['create', 'read', 'update']
            }
        },
        {
            'nom': 'CONTROLES',
            'description': 'Groupe de contrôles',
            'permissions': {
                'modules': ['proprietes', 'contrats'],
                'actions': ['read', 'update']
            }
        }
    ]
    
    groupes = {}
    for group_data in groupes_data:
        groupe, created = GroupeTravail.objects.get_or_create(
            nom=group_data['nom'],
            defaults={
                'description': group_data['description'],
                'permissions': group_data['permissions'],
                'actif': True
            }
        )
        groupes[group_data['nom']] = groupe
        print(f"✅ GroupeTravail: {group_data['nom']}")
    
    # Supprimer tous les utilisateurs existants
    User.objects.all().delete()
    print("🗑️ Tous les utilisateurs supprimés")
    
    # Créer les utilisateurs de test
    test_users = [
        {'username': 'admin', 'email': 'admin@example.com', 'password': 'admin123', 'groupe': 'ADMINISTRATION'},
        {'username': 'caisse1', 'email': 'caisse1@example.com', 'password': 'caisse123', 'groupe': 'CAISSE'},
        {'username': 'controle1', 'email': 'controle1@example.com', 'password': 'controle123', 'groupe': 'CONTROLES'},
        {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin123', 'groupe': 'ADMINISTRATION'},
        {'username': 'privilege1', 'email': 'privilege1@example.com', 'password': 'privilege123', 'groupe': 'PRIVILEGE'},
    ]
    
    for user_data in test_users:
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password']
        )
        user.is_staff = True
        user.groupe_travail = groupes[user_data['groupe']]
        user.save()
        print(f"✅ Utilisateur: {user_data['username']} créé avec groupe {user_data['groupe']}")
    
    # Test des connexions
    print("\n🔍 Test des connexions...")
    from django.contrib.auth import authenticate
    
    for user_data in test_users:
        user = authenticate(username=user_data['username'], password=user_data['password'])
        if user:
            print(f"✅ {user_data['username']}: Connexion réussie")
        else:
            print(f"❌ {user_data['username']}: Échec de connexion")
    
    print("\n🎉 Correction terminée !")

if __name__ == "__main__":
    fix_render()
