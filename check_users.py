#!/usr/bin/env python
"""
Script pour vérifier les utilisateurs existants
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

def check_users():
    """Vérifier les utilisateurs existants"""
    print("🔍 Vérification des utilisateurs...")
    
    # Lister tous les utilisateurs
    users = User.objects.all()
    print(f"📊 Nombre d'utilisateurs: {users.count()}")
    
    for user in users:
        groups = [group.name for group in user.groups.all()]
        print(f"  - {user.username} ({user.email}) - Groupes: {', '.join(groups)}")
        print(f"    Superuser: {user.is_superuser}, Staff: {user.is_staff}")
    
    # Test des connexions
    print("\n🔐 Test des connexions...")
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
            print(f"✅ {username}: Connexion réussie")
        else:
            print(f"❌ {username}: Échec de connexion")

if __name__ == "__main__":
    check_users()
