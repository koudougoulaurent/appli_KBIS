#!/usr/bin/env python
"""
Script pour tester les permissions et créer un utilisateur avec les bonnes permissions
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
from django.contrib.auth.models import Group
from django.test import Client
from core.utils import check_group_permissions

User = get_user_model()


def test_permissions():
    """Test des permissions et création d'utilisateur avec bonnes permissions"""
    print("=== TEST PERMISSIONS ===\n")
    
    # Test 1: Vérifier les groupes existants
    print("1. Verification des groupes existants...")
    try:
        groups = Group.objects.all()
        print(f"   Nombre de groupes: {groups.count()}")
        for group in groups:
            print(f"   - {group.name}")
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print()
    
    # Test 2: Créer un utilisateur avec les bonnes permissions
    print("2. Creation d'un utilisateur avec permissions...")
    try:
        # Créer ou récupérer l'utilisateur
        user, created = User.objects.get_or_create(
            username='admin_debug',
            defaults={
                'email': 'admin@debug.com',
                'first_name': 'Admin',
                'last_name': 'Debug',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            print("   [OK] Utilisateur admin cree")
        else:
            print("   [OK] Utilisateur admin existe deja")
        
        # Ajouter aux groupes nécessaires
        try:
            privilege_group = Group.objects.get(name='PRIVILEGE')
            user.groups.add(privilege_group)
            print("   [OK] Ajoute au groupe PRIVILEGE")
        except Group.DoesNotExist:
            print("   [ATTENTION] Groupe PRIVILEGE non trouve")
        
        try:
            admin_group = Group.objects.get(name='ADMINISTRATION')
            user.groups.add(admin_group)
            print("   [OK] Ajoute au groupe ADMINISTRATION")
        except Group.DoesNotExist:
            print("   [ATTENTION] Groupe ADMINISTRATION non trouve")
        
        print(f"   Utilisateur: {user.username} (ID: {user.id})")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Groupes: {[g.name for g in user.groups.all()]}")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Test 3: Tester les permissions
    print("3. Test des permissions...")
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
    
    # Test 4: Test de génération via client Django
    print("4. Test de generation via client Django...")
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
                    with open('test_permissions_response.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("   Fichier sauvegarde: test_permissions_response.html")
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
    
    print("\n=== FIN TESTS ===")


if __name__ == "__main__":
    test_permissions()

