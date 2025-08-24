#!/usr/bin/env python
"""
Script pour créer un utilisateur de test et les groupes de travail
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from django.db import transaction
from django.contrib.auth.hashers import make_password

def setup_test_environment():
    """Créer l'environnement de test complet"""
    
    print("🚀 Configuration de l'environnement de test...")
    
    with transaction.atomic():
        # 1. Créer les groupes de travail
        print("👥 Création des groupes de travail...")
        
        groups_data = [
            {
                'nom': 'CAISSE',
                'description': 'Gestion des paiements et retraits',
                'actif': True
            },
            {
                'nom': 'CONTROLES',
                'description': 'Contrôle et audit des opérations',
                'actif': True
            },
            {
                'nom': 'ADMINISTRATION',
                'description': 'Gestion administrative et configuration',
                'actif': True
            },
            {
                'nom': 'PRIVILEGE',
                'description': 'Accès complet à toutes les fonctionnalités',
                'actif': True
            }
        ]
        
        created_groups = {}
        for group_data in groups_data:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults={
                    'description': group_data['description'],
                    'actif': group_data['actif']
                }
            )
            
            if created:
                print(f"✅ Groupe {groupe.nom} créé: {groupe.description}")
            else:
                print(f"ℹ️  Groupe {groupe.nom} existe déjà: {groupe.description}")
            
            created_groups[groupe.nom] = groupe
        
        # 2. Créer un utilisateur de test pour chaque groupe
        print("\n👤 Création des utilisateurs de test...")
        
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@gestimmob.fr',
                'password': 'admin123',
                'first_name': 'Administrateur',
                'last_name': 'Système',
                'groupe': 'PRIVILEGE',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'caisse',
                'email': 'caisse@gestimmob.fr',
                'password': 'caisse123',
                'first_name': 'Utilisateur',
                'last_name': 'Caisse',
                'groupe': 'CAISSE'
            },
            {
                'username': 'controles',
                'email': 'controles@gestimmob.fr',
                'password': 'controles123',
                'first_name': 'Utilisateur',
                'last_name': 'Contrôles',
                'groupe': 'CONTROLES'
            },
            {
                'username': 'admin_groupe',
                'email': 'admin_groupe@gestimmob.fr',
                'password': 'admin123',
                'first_name': 'Utilisateur',
                'last_name': 'Administration',
                'groupe': 'ADMINISTRATION'
            }
        ]
        
        created_users = []
        for user_data in test_users:
            username = user_data['username']
            
            # Vérifier si l'utilisateur existe déjà
            if Utilisateur.objects.filter(username=username).exists():
                print(f"ℹ️  Utilisateur {username} existe déjà")
                continue
            
            # Créer l'utilisateur
            user = Utilisateur.objects.create(
                username=username,
                email=user_data['email'],
                password=make_password(user_data['password']),
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                groupe_travail=created_groups[user_data['groupe']],
                actif=True,
                is_staff=user_data.get('is_staff', False),
                is_superuser=user_data.get('is_superuser', False)
            )
            
            print(f"✅ Utilisateur {username} créé (groupe: {user_data['groupe']})")
            created_users.append(user)
    
    print("\n🎉 Configuration terminée avec succès!")
    print("\n📊 Résumé:")
    print(f"   - Groupes créés: {len(created_groups)}")
    print(f"   - Utilisateurs créés: {len(created_users)}")
    
    print("\n🔑 Informations de connexion:")
    print("   - Admin (PRIVILEGE): admin / admin123")
    print("   - Caisse: caisse / caisse123")
    print("   - Contrôles: controles / controles123")
    print("   - Administration: admin_groupe / admin123")
    
    print("\n🌐 Accès:")
    print("   - Application: http://127.0.0.1:8000/")
    print("   - Admin Django: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    try:
        setup_test_environment()
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
