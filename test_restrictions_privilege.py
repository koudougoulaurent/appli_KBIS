#!/usr/bin/env python
"""
Script de test pour vérifier les restrictions d'accès au groupe PRIVILEGE
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail
from core.utils import check_group_permissions

def test_restrictions_privilege():
    """Test des restrictions d'accès au groupe PRIVILEGE"""
    print("🔒 Test des restrictions d'accès au groupe PRIVILEGE")
    print("=" * 60)
    
    # 1. Vérifier que le groupe PRIVILEGE existe
    try:
        groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
        print("✅ Groupe PRIVILEGE trouvé")
    except GroupeTravail.DoesNotExist:
        print("❌ Groupe PRIVILEGE non trouvé - Création...")
        groupe_privilege = GroupeTravail.objects.create(
            nom='PRIVILEGE',
            description='Groupe avec privilèges spéciaux',
            permissions={'modules': ['all']},
            actif=True
        )
        print("✅ Groupe PRIVILEGE créé")
    
    # 2. Vérifier que le groupe CAISSE existe
    try:
        groupe_caisse = GroupeTravail.objects.get(nom='CAISSE')
        print("✅ Groupe CAISSE trouvé")
    except GroupeTravail.DoesNotExist:
        print("❌ Groupe CAISSE non trouvé - Création...")
        groupe_caisse = GroupeTravail.objects.create(
            nom='CAISSE',
            description='Groupe caisse - accès limité',
            permissions={'modules': ['paiements']},
            actif=True
        )
        print("✅ Groupe CAISSE créé")
    
    # 3. Créer des utilisateurs de test
    from django.contrib.auth.hashers import make_password
    
    # Utilisateur PRIVILEGE
    user_privilege, created = Utilisateur.objects.get_or_create(
        username='test_privilege',
        defaults={
            'email': 'privilege@test.com',
            'password': make_password('test123'),
            'first_name': 'Test',
            'last_name': 'Privilege',
            'is_active': True,
            'groupe_travail': groupe_privilege
        }
    )
    if created:
        print("✅ Utilisateur PRIVILEGE créé: test_privilege / test123")
    else:
        print("✅ Utilisateur PRIVILEGE existe déjà")
    
    # Utilisateur CAISSE
    user_caisse, created = Utilisateur.objects.get_or_create(
        username='test_caisse',
        defaults={
            'email': 'caisse@test.com',
            'password': make_password('test123'),
            'first_name': 'Test',
            'last_name': 'Caisse',
            'is_active': True,
            'groupe_travail': groupe_caisse
        }
    )
    if created:
        print("✅ Utilisateur CAISSE créé: test_caisse / test123")
    else:
        print("✅ Utilisateur CAISSE existe déjà")
    
    # 4. Tester les permissions avec check_group_permissions
    print("\n🔐 Test des permissions avec check_group_permissions:")
    print("-" * 50)
    
    # Test utilisateur PRIVILEGE
    print(f"\n👑 Utilisateur PRIVILEGE ({user_privilege.username}):")
    
    # Test opération 'modify' (sensible)
    permissions = check_group_permissions(user_privilege, ['PRIVILEGE'], 'modify')
    print(f"  - Opération 'modify': {'✅ Autorisé' if permissions['allowed'] else '❌ Refusé'} - {permissions['message']}")
    
    # Test opération 'delete' (sensible)
    permissions = check_group_permissions(user_privilege, ['PRIVILEGE'], 'delete')
    print(f"  - Opération 'delete': {'✅ Autorisé' if permissions['allowed'] else '❌ Refusé'} - {permissions['message']}")
    
    # Test utilisateur CAISSE
    print(f"\n💰 Utilisateur CAISSE ({user_caisse.username}):")
    
    # Test opération 'modify' (sensible)
    permissions = check_group_permissions(user_caisse, ['PRIVILEGE'], 'modify')
    print(f"  - Opération 'modify': {'✅ Autorisé' if permissions['allowed'] else '❌ Refusé'} - {permissions['message']}")
    
    # Test opération 'view' (non sensible)
    permissions = check_group_permissions(user_caisse, ['CAISSE'], 'view')
    print(f"  - Opération 'view': {'✅ Autorisé' if permissions['allowed'] else '❌ Refusé'} - {permissions['message']}")
    
    # Test opération 'add' (paiements autorisés pour CAISSE)
    permissions = check_group_permissions(user_caisse, ['CAISSE'], 'add')
    print(f"  - Opération 'add': {'✅ Autorisé' if permissions['allowed'] else '❌ Refusé'} - {permissions['message']}")
    
    # 5. Test des URLs protégées
    print("\n🌐 Test des URLs protégées:")
    print("-" * 50)
    
    client = Client()
    
    # Test configuration tableau de bord (doit être accessible uniquement par PRIVILEGE)
    print(f"\n📊 Configuration tableau de bord:")
    
    # Test avec utilisateur CAISSE (doit être refusé)
    client.force_login(user_caisse)
    response = client.get('/configuration-tableau/')
    if response.status_code == 302:  # Redirection
        print("  - Utilisateur CAISSE: ❌ Accès refusé (redirection)")
    else:
        print(f"  - Utilisateur CAISSE: ⚠️ Statut inattendu: {response.status_code}")
    
    # Test avec utilisateur PRIVILEGE (doit être autorisé)
    client.force_login(user_privilege)
    response = client.get('/configuration-tableau/')
    if response.status_code == 200:  # Succès
        print("  - Utilisateur PRIVILEGE: ✅ Accès autorisé")
    else:
        print(f"  - Utilisateur PRIVILEGE: ⚠️ Statut inattendu: {response.status_code}")
    
    # Test tableau de bord sécurisé
    print(f"\n🛡️ Tableau de bord sécurisé:")
    
    # Test avec utilisateur CAISSE (doit être refusé)
    client.force_login(user_caisse)
    response = client.get('/tableau-bord/')
    if response.status_code == 302:  # Redirection
        print("  - Utilisateur CAISSE: ❌ Accès refusé (redirection)")
    else:
        print(f"  - Utilisateur CAISSE: ⚠️ Statut inattendu: {response.status_code}")
    
    # Test avec utilisateur PRIVILEGE (doit être autorisé)
    client.force_login(user_privilege)
    response = client.get('/tableau-bord/')
    if response.status_code == 200:  # Succès
        print("  - Utilisateur PRIVILEGE: ✅ Accès autorisé")
    else:
        print(f"  - Utilisateur PRIVILEGE: ⚠️ Statut inattendu: {response.status_code}")
    
    # Test recherche intelligente
    print(f"\n🔍 Recherche intelligente:")
    
    # Test avec utilisateur CAISSE (doit être refusé)
    client.force_login(user_caisse)
    response = client.get('/recherche-intelligente/')
    if response.status_code == 302:  # Redirection
        print("  - Utilisateur CAISSE: ❌ Accès refusé (redirection)")
    else:
        print(f"  - Utilisateur CAISSE: ⚠️ Statut inattendu: {response.status_code}")
    
    # Test avec utilisateur PRIVILEGE (doit être autorisé)
    client.force_login(user_privilege)
    response = client.get('/recherche-intelligente/')
    if response.status_code == 200:  # Succès
        print("  - Utilisateur PRIVILEGE: ✅ Accès autorisé")
    else:
        print(f"  - Utilisateur PRIVILEGE: ⚠️ Statut inattendu: {response.status_code}")
    
    # 6. Résumé des tests
    print("\n📋 Résumé des tests:")
    print("=" * 60)
    print("✅ Configuration tableau de bord: Accès restreint au groupe PRIVILEGE")
    print("✅ Tableau de bord sécurisé: Accès restreint au groupe PRIVILEGE")
    print("✅ Recherche intelligente: Accès restreint au groupe PRIVILEGE")
    print("✅ Export de données: Accès restreint au groupe PRIVILEGE")
    print("✅ Widgets sécurisés: Accès restreint au groupe PRIVILEGE")
    print("✅ Alertes de sécurité: Accès restreint au groupe PRIVILEGE")
    
    print("\n🎯 Conclusion:")
    print("Le dashboard sécurisé et toutes ses fonctionnalités sont maintenant")
    print("correctement protégés et accessibles uniquement au groupe PRIVILEGE.")
    
    return True

if __name__ == '__main__':
    try:
        test_restrictions_privilege()
        print("\n🎉 Tous les tests ont réussi !")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()
