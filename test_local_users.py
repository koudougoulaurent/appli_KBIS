#!/usr/bin/env python
"""
Script de test local pour vérifier la création des utilisateurs de test.
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail

User = get_user_model()

def test_users_creation():
    """Test la création des utilisateurs de test."""
    print("🧪 TEST DE CRÉATION DES UTILISATEURS")
    print("=" * 50)
    
    try:
        # Créer les utilisateurs de test
        print("👥 Création des utilisateurs de test...")
        call_command('create_test_users', '--force')
        
        # Vérifier que les utilisateurs ont été créés
        print("\n🔍 Vérification des utilisateurs créés:")
        test_usernames = ['admin', 'caisse', 'admin_immobilier', 'controleur', 'test']
        
        for username in test_usernames:
            try:
                user = User.objects.get(username=username)
                print(f"✅ {username}: {user.first_name} {user.last_name} (Groupe: {user.groupe_travail.nom if user.groupe_travail else 'Aucun'})")
            except User.DoesNotExist:
                print(f"❌ {username}: Non trouvé")
        
        # Vérifier les groupes
        print("\n🔍 Vérification des groupes créés:")
        groupes = GroupeTravail.objects.all()
        for groupe in groupes:
            print(f"✅ Groupe {groupe.nom}: {groupe.description}")
        
        # Test de connexion
        print("\n🔐 Test de connexion:")
        from django.test import Client
        client = Client()
        
        # Test avec admin
        login_success = client.login(username='admin', password='admin123')
        if login_success:
            print("✅ Connexion admin réussie")
        else:
            print("❌ Connexion admin échouée")
        
        # Test avec caisse
        login_success = client.login(username='caisse', password='caisse123')
        if login_success:
            print("✅ Connexion caisse réussie")
        else:
            print("❌ Connexion caisse échouée")
        
        print("\n🎉 TEST TERMINÉ AVEC SUCCÈS!")
        
    except Exception as e:
        print(f"❌ ERREUR LORS DU TEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_users_creation()
