#!/usr/bin/env python
"""
Script de test simplifié pour vérifier les permissions dans la plateforme.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.utils import check_group_permissions
from utilisateurs.models import Utilisateur, GroupeTravail

def test_permissions():
    """Test des permissions pour tous les groupes."""
    print("🔐 TEST DES PERMISSIONS SIMPLIFIÉ")
    print("=" * 50)
    
    try:
        # Créer ou récupérer les groupes de travail
        groupes = {}
        for nom_groupe in ['PAIEMENT', 'ADMINISTRATION', 'PRIVILEGE']:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=nom_groupe,
                defaults={
                    'description': f'Groupe {nom_groupe}',
                    'permissions': {'modules': []},
                    'actif': True
                }
            )
            groupes[nom_groupe] = groupe
            print(f"✅ Groupe de travail {nom_groupe} créé/récupéré avec succès")
        
        # Créer des utilisateurs de test
        users = {}
        for nom_groupe in ['PAIEMENT', 'ADMINISTRATION', 'PRIVILEGE']:
            username = f'test_{nom_groupe.lower()}'
            user, created = Utilisateur.objects.get_or_create(
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
            
            # Assigner au groupe de travail
            user.groupe_travail = groupes[nom_groupe]
            user.save()
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
            ('ADMINISTRATION', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un bailleur'),
            ('ADMINISTRATION', 'modify', ['PRIVILEGE'], 'Modifier un bailleur'),
            ('ADMINISTRATION', 'delete', ['PRIVILEGE'], 'Supprimer un bailleur'),
            ('PRIVILEGE', 'add', ['PRIVILEGE', 'ADMINISTRATION'], 'Ajouter un bailleur'),
            ('PRIVILEGE', 'modify', ['PRIVILEGE'], 'Modifier un bailleur'),
            ('PRIVILEGE', 'delete', ['PRIVILEGE'], 'Supprimer un bailleur'),
        ]
        
        violations = 0
        total_tests = 0
        
        for groupe_test, operation, groupes_autorises, description in test_cases:
            total_tests += 1
            user = users[groupe_test]
            
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
        
    except Exception as e:
        print(f"💥 ERREUR LORS DES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = test_permissions()
        
        if success:
            print("\n🎯 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
            sys.exit(0)
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
