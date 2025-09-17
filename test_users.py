#!/usr/bin/env python
"""
Script de test pour vérifier les utilisateurs créés
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

def test_users():
    """Tester les utilisateurs créés"""
    print("🔍 Test des utilisateurs créés...")
    
    # Vérifier les groupes
    groups = Group.objects.all()
    print(f"📊 Groupes créés: {groups.count()}")
    for group in groups:
        print(f"  - {group.name}")
    
    # Vérifier les utilisateurs
    users = User.objects.all()
    print(f"\n👥 Utilisateurs créés: {users.count()}")
    
    for user in users:
        user_groups = [group.name for group in user.groups.all()]
        print(f"  - {user.username} ({user.email}) - Groupes: {', '.join(user_groups)}")
        print(f"    Superuser: {user.is_superuser}, Staff: {user.is_staff}")
    
    # Test de connexion
    print(f"\n🔐 Test de connexion:")
    test_credentials = [
        ('admin', 'admin123'),
        ('caisse1', 'caisse123'),
        ('controle1', 'controle123'),
    ]
    
    for username, password in test_credentials:
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user:
            print(f"  ✅ {username}: Connexion réussie")
        else:
            print(f"  ❌ {username}: Échec de connexion")
    
    print("\n🎉 Test terminé !")

if __name__ == "__main__":
    test_users()
