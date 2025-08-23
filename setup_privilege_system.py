#!/usr/bin/env python
"""
Script de configuration et test du système de privilège
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from utilisateurs.models import Utilisateur, GroupeTravail, AuditLog
from proprietes.models import Bailleur, Locataire, Propriete
from django.contrib.auth.hashers import make_password

def setup_privilege_system():
    """Configuration du système de privilège"""
    print("🔧 Configuration du système de privilège...")
    
    # 1. Créer le groupe de travail PRIVILEGE s'il n'existe pas
    privilege_groupe_travail, created = GroupeTravail.objects.get_or_create(
        nom='PRIVILEGE',
        defaults={
            'description': 'Groupe avec privilèges spéciaux pour la suppression conditionnelle et la gestion des profils',
            'permissions': {'modules': ['all']},
            'actif': True
        }
    )
    if created:
        print("✅ Groupe de travail PRIVILEGE créé")
    else:
        print("✅ Groupe de travail PRIVILEGE existe déjà")
    
    # 2. Créer un utilisateur de test PRIVILEGE
    privilege_user, created = Utilisateur.objects.get_or_create(
        username='admin_privilege',
        defaults={
            'email': 'admin_privilege@example.com',
            'password': make_password('admin123'),
            'first_name': 'Admin',
            'last_name': 'Privilege',
            'is_active': True,
            'is_staff': True,
            'is_superuser': False,
            'groupe_travail': privilege_groupe_travail
        }
    )
    
    if created:
        print("✅ Utilisateur PRIVILEGE créé: admin_privilege / admin123")
    else:
        # Mettre à jour le groupe de travail si l'utilisateur existe déjà
        privilege_user.groupe_travail = privilege_groupe_travail
        privilege_user.save()
        print("✅ Utilisateur PRIVILEGE mis à jour")
    
    # 3. Créer un utilisateur normal pour comparaison
    normal_user, created = Utilisateur.objects.get_or_create(
        username='user_normal',
        defaults={
            'email': 'user_normal@example.com',
            'password': make_password('user123'),
            'first_name': 'User',
            'last_name': 'Normal',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
            'groupe_travail': None
        }
    )
    
    if created:
        print("✅ Utilisateur normal créé: user_normal / user123")
    else:
        print("✅ Utilisateur normal existe déjà")
    
    # 4. Créer quelques données de test
    print("\n📊 Création de données de test...")
    
    # Créer un bailleur
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Test Bailleur',
        defaults={
            'prenom': 'Jean',
            'email': 'jean@test.com',
            'telephone': '0123456789'
        }
    )
    
    # Créer un locataire
    locataire, created = Locataire.objects.get_or_create(
        nom='Test Locataire',
        defaults={
            'prenom': 'Marie',
            'email': 'marie@test.com',
            'telephone': '0987654321'
        }
    )
    
    # Créer une propriété
    propriete, created = Propriete.objects.get_or_create(
        titre='Appartement Test',
        defaults={
            'adresse': '123 Rue Test',
            'ville': 'Paris',
            'code_postal': '75001',
            'loyer_actuel': 1000,
            'disponible': True
        }
    )
    
    print("✅ Données de test créées")
    
    # 5. Tester les fonctionnalités
    print("\n🧪 Test des fonctionnalités...")
    
    # Test is_privilege_user
    is_privilege = privilege_user.is_privilege_user()
    print(f"✅ Test is_privilege_user: {is_privilege}")
    
    # Test can_delete_any_element
    can_delete_bailleur = privilege_user.can_delete_any_element(bailleur)
    can_delete_locataire = privilege_user.can_delete_any_element(locataire)
    can_delete_propriete = privilege_user.can_delete_any_element(propriete)
    
    print(f"✅ Test can_delete_any_element - Bailleur: {can_delete_bailleur}")
    print(f"✅ Test can_delete_any_element - Locataire: {can_delete_locataire}")
    print(f"✅ Test can_delete_any_element - Propriété: {can_delete_propriete}")
    
    # 6. Afficher les URLs disponibles
    print("\n🌐 URLs du système de privilège:")
    print("http://127.0.0.1:8000/utilisateurs/dashboard-privilege/")
    print("http://127.0.0.1:8000/utilisateurs/privilege/elements/")
    print("http://127.0.0.1:8000/utilisateurs/privilege/profiles/")
    print("http://127.0.0.1:8000/utilisateurs/privilege/audit-log/")
    
    print("\n🔑 Identifiants de connexion:")
    print("Utilisateur PRIVILEGE: admin_privilege / admin123")
    print("Utilisateur normal: user_normal / user123")
    
    print("\n✅ Configuration terminée !")
    print("Connectez-vous avec admin_privilege pour accéder aux fonctionnalités de privilège.")

if __name__ == '__main__':
    setup_privilege_system() 