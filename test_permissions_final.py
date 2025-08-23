#!/usr/bin/env python
"""
Script de test final pour vérifier les permissions dans toute la plateforme.
Teste que les groupes ADMINISTRATION et PRIVILEGE ont les bonnes permissions.
"""

import os
import sys
import django
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.utils import check_group_permissions
from proprietes.models import Bailleur, Locataire, Propriete, TypeBien
from contrats.models import Contrat, Quittance, EtatLieux
from paiements.models import Paiement, Retrait, CompteBancaire, ChargeDeductible
from utilisateurs.models import Utilisateur

def test_permissions():
    """Test des permissions pour tous les groupes."""
    print("🔐 TEST DES PERMISSIONS FINAL")
    print("=" * 50)
    
    # Créer des utilisateurs de test pour chaque groupe
    factory = RequestFactory()
    
    # Créer ou récupérer les groupes
    groupe_paiement, _ = Group.objects.get_or_create(name='PAIEMENT')
    groupe_administration, _ = Group.objects.get_or_create(name='ADMINISTRATION')
    groupe_privilege, _ = Group.objects.get_or_create(name='PRIVILEGE')
    
    # Créer des utilisateurs de test
    users = {}
    for nom_groupe in ['PAIEMENT', 'ADMINISTRATION', 'PRIVILEGE']:
        username = f'test_{nom_groupe.lower()}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@test.com',
                'first_name': f'Test {nom_groupe}',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Assigner au groupe
        user.groups.clear()
        user.groups.add(Group.objects.get(name=nom_groupe))
        users[nom_groupe] = user
        print(f"✅ Utilisateur {username} créé et assigné au groupe {nom_groupe}")
    
    print("\n🧪 TEST DES PERMISSIONS PAR GROUPE")
    print("-" * 40)
    
    # Test des permissions pour chaque groupe
    test_cases = [
        # (groupe, opération, groupes_autorises, description)
        ('PAIEMENT', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un bailleur'),
        ('PAIEMENT', 'modify', ['PRIVILEGE'], 'Modifier un bailleur'),
        ('PAIEMENT', 'delete', ['PRIVILEGE'], 'Supprimer un bailleur'),
        ('PAIEMENT', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un locataire'),
        ('PAIEMENT', 'modify', ['PRIVILEGE'], 'Modifier un locataire'),
        ('PAIEMENT', 'delete', ['PRIVILEGE'], 'Supprimer un locataire'),
        ('PAIEMENT', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un paiement'),
        ('PAIEMENT', 'modify', ['PRIVILEGE'], 'Modifier un paiement'),
        ('PAIEMENT', 'delete', ['PRIVILEGE'], 'Supprimer un paiement'),
        ('ADMINISTRATION', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un bailleur'),
        ('ADMINISTRATION', 'modify', ['PRIVILEGE'], 'Modifier un bailleur'),
        ('ADMINISTRATION', 'delete', ['PRIVILEGE'], 'Supprimer un bailleur'),
        ('ADMINISTRATION', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un template'),
        ('ADMINISTRATION', 'modify', ['PRIVILEGE'], 'Modifier un template'),
        ('ADMINISTRATION', 'delete', ['PRIVILEGE'], 'Supprimer un template'),
        ('PRIVILEGE', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un bailleur'),
        ('PRIVILEGE', 'modify', ['PRIVILEGE'], 'Modifier un bailleur'),
        ('PRIVILEGE', 'delete', ['PRIVILEGE'], 'Supprimer un bailleur'),
    ]
    
    violations = 0
    total_tests = 0
    
    for groupe_test, operation, groupes_autorises, description in test_cases:
        total_tests += 1
        user = users[groupe_test]
        
        # Simuler une requête
        request = factory.get('/')
        request.user = user
        
        # Tester les permissions
        permissions = check_group_permissions(user, groupes_autorises, operation)
        
        if permissions['allowed']:
            print(f"✅ {groupe_test} - {description}: AUTORISÉ")
        else:
            print(f"❌ {groupe_test} - {description}: REFUSÉ - {permissions['message']}")
            violations += 1
    
    print(f"\n📊 RÉSULTATS FINAUX")
    print(f"Total des tests: {total_tests}")
    print(f"Violations: {violations}")
    print(f"Taux de succès: {((total_tests - violations) / total_tests * 100):.1f}%")
    
    if violations == 0:
        print("🎉 TOUTES LES PERMISSIONS SONT CORRECTEMENT CONFIGURÉES !")
    else:
        print(f"⚠️  {violations} violation(s) détectée(s)")
    
    return violations == 0

def test_specific_views():
    """Test des vues spécifiques pour vérifier les redirections."""
    print("\n🔍 TEST DES VUES SPÉCIFIQUES")
    print("-" * 40)
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_view',
        defaults={'email': 'test@test.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Assigner au groupe PAIEMENT
    user.groups.clear()
    user.groups.add(Group.objects.get(name='PAIEMENT'))
    
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    # Test de la fonction check_group_permissions
    print("Test de check_group_permissions...")
    
    # Test ajout (devrait être autorisé pour ADMINISTRATION et PRIVILEGE)
    permissions = check_group_permissions(user, ['PRIVILEGE', 'ADMINISTRATION'], 'add')
    print(f"PAIEMENT - Ajout: {'✅ AUTORISÉ' if permissions['allowed'] else '❌ REFUSÉ'}")
    
    # Test modification (devrait être refusé pour PAIEMENT)
    permissions = check_group_permissions(user, ['PRIVILEGE'], 'modify')
    print(f"PAIEMENT - Modification: {'✅ AUTORISÉ' if permissions['allowed'] else '❌ REFUSÉ'}")
    
    # Test suppression (devrait être refusé pour PAIEMENT)
    permissions = check_group_permissions(user, ['PRIVILEGE'], 'delete')
    print(f"PAIEMENT - Suppression: {'✅ AUTORISÉ' if permissions['allowed'] else '❌ REFUSÉ'}")

if __name__ == '__main__':
    try:
        success = test_permissions()
        test_specific_views()
        
        if success:
            print("\n🎯 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
            sys.exit(0)
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
