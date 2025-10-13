#!/usr/bin/env python
"""
Script pour corriger les permissions de l'utilisateur
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement, QuittancePaiement
from django.contrib.auth import get_user_model
from django.test import Client
from core.utils import check_group_permissions

User = get_user_model()


def fix_user_permissions():
    """Corriger les permissions de l'utilisateur"""
    print("=== CORRECTION PERMISSIONS UTILISATEUR ===\n")
    
    # Test 1: Vérifier les groupes de travail existants
    print("1. Verification des groupes de travail...")
    try:
        from utilisateurs.models import GroupeTravail
        
        groupes = GroupeTravail.objects.all()
        print(f"   Nombre de groupes de travail: {groupes.count()}")
        for groupe in groupes:
            print(f"   - {groupe.nom}: {groupe.description}")
    except Exception as e:
        print(f"   [ERREUR] {e}")
        return
    
    print()
    
    # Test 2: Créer ou récupérer le groupe PRIVILEGE
    print("2. Creation/recuperation du groupe PRIVILEGE...")
    try:
        groupe_privilege, created = GroupeTravail.objects.get_or_create(
            nom='PRIVILEGE',
            defaults={
                'description': 'Groupe avec tous les privilèges',
                'permissions': {
                    'paiements': ['add', 'modify', 'delete', 'view', 'validate'],
                    'contrats': ['add', 'modify', 'delete', 'view', 'validate'],
                    'proprietes': ['add', 'modify', 'delete', 'view', 'validate'],
                    'utilisateurs': ['add', 'modify', 'delete', 'view', 'validate'],
                },
                'actif': True
            }
        )
        
        if created:
            print("   [OK] Groupe PRIVILEGE cree")
        else:
            print("   [OK] Groupe PRIVILEGE existe deja")
        
        print(f"   Groupe: {groupe_privilege.nom} (ID: {groupe_privilege.id})")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
        return
    
    print()
    
    # Test 3: Créer ou récupérer l'utilisateur admin
    print("3. Creation/recuperation de l'utilisateur admin...")
    try:
        user, created = User.objects.get_or_create(
            username='admin_debug',
            defaults={
                'email': 'admin@debug.com',
                'first_name': 'Admin',
                'last_name': 'Debug',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
                'groupe_travail': groupe_privilege,
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            print("   [OK] Utilisateur admin cree")
        else:
            # Mettre à jour le groupe de travail
            user.groupe_travail = groupe_privilege
            user.save()
            print("   [OK] Utilisateur admin mis a jour")
        
        print(f"   Utilisateur: {user.username} (ID: {user.id})")
        print(f"   Groupe de travail: {user.groupe_travail.nom if user.groupe_travail else 'Aucun'}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Staff: {user.is_staff}")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Test 4: Tester les permissions
    print("4. Test des permissions...")
    try:
        # Test permission view
        permissions_view = check_group_permissions(user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
        print(f"   Permission view: {permissions_view['allowed']} - {permissions_view['message']}")
        
        # Test permission add
        permissions_add = check_group_permissions(user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'add')
        print(f"   Permission add: {permissions_add['allowed']} - {permissions_add['message']}")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print()
    
    # Test 5: Test de génération via client Django
    print("5. Test de generation via client Django...")
    try:
        client = Client()
        
        # Se connecter
        login_success = client.login(username='admin_debug', password='admin123')
        print(f"   Connexion: {'OK' if login_success else 'ECHEC'}")
        
        if login_success:
            # Récupérer un paiement et créer une quittance
            paiement = Paiement.objects.filter(statut='valide').first()
            if paiement:
                print(f"   Paiement: ID {paiement.id}")
                
                # Supprimer l'ancienne quittance si elle existe
                if hasattr(paiement, 'quittance'):
                    paiement.quittance.delete()
                
                # Créer une nouvelle quittance
                quittance = QuittancePaiement.objects.create(
                    paiement=paiement,
                    cree_par=user
                )
                print(f"   Quittance: {quittance.numero_quittance}")
                
                # Tester l'URL de la quittance
                url = f'/paiements/quittance/{quittance.id}/'
                print(f"   URL: {url}")
                
                response = client.get(url)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   [OK] Page accessible")
                    
                    content = response.content.decode('utf-8')
                    print(f"   Taille: {len(content)} caracteres")
                    
                    if 'data:image/png;base64' in content:
                        print("   [OK] Image base64 presente")
                    else:
                        print("   [ATTENTION] Image base64 manquante")
                    
                    # Sauvegarder
                    with open('test_fixed_permissions.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("   Fichier sauvegarde: test_fixed_permissions.html")
                else:
                    print(f"   [ATTENTION] Status: {response.status_code}")
                    print(f"   Contenu: {response.content.decode('utf-8')[:200]}...")
            else:
                print("   [ERREUR] Aucun paiement valide trouve")
        else:
            print("   [ERREUR] Impossible de se connecter")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== FIN CORRECTION ===")


if __name__ == "__main__":
    fix_user_permissions()

