#!/usr/bin/env python
"""
Script de test pour vérifier la connexion des utilisateurs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

def test_login():
    """Tester la connexion des utilisateurs"""
    print("🔐 Test de connexion des utilisateurs...")
    
    # Créer les groupes d'abord
    groups = ['ADMINISTRATION', 'PRIVILEGE', 'CAISSE', 'CONTROLES']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        print(f"✅ Groupe: {group_name}")
    
    # Créer l'admin
    try:
        admin = User.objects.get(username='admin')
        admin.delete()
        print("🗑️ Ancien admin supprimé")
    except User.DoesNotExist:
        pass
    
    admin = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
    print("✅ Admin créé")
    
    # Ajouter admin au groupe ADMINISTRATION
    admin_group = Group.objects.get(name='ADMINISTRATION')
    admin.groups.add(admin_group)
    
    # Créer les utilisateurs de test
    test_users = [
        {'username': 'caisse1', 'email': 'caisse1@example.com', 'password': 'caisse123', 'groups': ['CAISSE']},
        {'username': 'controle1', 'email': 'controle1@example.com', 'password': 'controle123', 'groups': ['CONTROLES']},
        {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin123', 'groups': ['ADMINISTRATION']},
        {'username': 'privilege1', 'email': 'privilege1@example.com', 'password': 'privilege123', 'groups': ['PRIVILEGE']},
    ]
    
    for user_data in test_users:
        try:
            existing_user = User.objects.get(username=user_data['username'])
            existing_user.delete()
            print(f"🗑️ Ancien {user_data['username']} supprimé")
        except User.DoesNotExist:
            pass
        
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password']
        )
        user.is_staff = True
        user.save()
        
        for group_name in user_data['groups']:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        
        print(f"✅ {user_data['username']} créé")
    
    # Tester les connexions
    print("\n🔍 Test des connexions...")
    test_credentials = [
        ('admin', 'admin123'),
        ('caisse1', 'caisse123'),
        ('controle1', 'controle123'),
        ('admin1', 'admin123'),
        ('privilege1', 'privilege123'),
    ]
    
    for username, password in test_credentials:
        user = authenticate(username=username, password=password)
        if user:
            groups = [group.name for group in user.groups.all()]
            print(f"✅ {username}: Connexion réussie - Groupes: {', '.join(groups)}")
        else:
            print(f"❌ {username}: Échec de connexion")
    
    print("\n🎉 Test terminé !")

if __name__ == "__main__":
    test_login()
