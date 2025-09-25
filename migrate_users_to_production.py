#!/usr/bin/env python
"""
Script pour migrer les utilisateurs de test vers la base de production
Utilisez ce script pour créer les utilisateurs directement dans PostgreSQL
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from core.models import ConfigurationEntreprise

User = get_user_model()

def create_production_users():
    """Crée les utilisateurs de test en production"""
    print("🚀 Création des utilisateurs de test en production...")
    
    # Utilisateurs de test avec groupes
    test_users = [
        {
            'username': 'admin',
            'email': 'admin@kbis.bf',
            'password': 'admin123',
            'first_name': 'Administrateur',
            'last_name': 'Système',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'groups': ['ADMINISTRATION', 'PRIVILEGE']
        },
        {
            'username': 'gestionnaire',
            'email': 'gestionnaire@kbis.bf',
            'password': 'gestion123',
            'first_name': 'Jean',
            'last_name': 'Gestionnaire',
            'is_staff': True,
            'is_superuser': False,
            'is_active': True,
            'groups': ['ADMINISTRATION']
        },
        {
            'username': 'agent',
            'email': 'agent@kbis.bf',
            'password': 'agent123',
            'first_name': 'Marie',
            'last_name': 'Agent',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True,
            'groups': ['PRIVILEGE']
        },
        {
            'username': 'comptable',
            'email': 'comptable@kbis.bf',
            'password': 'comptable123',
            'first_name': 'Paul',
            'last_name': 'Comptable',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True,
            'groups': ['CAISSE']
        },
        {
            'username': 'demo',
            'email': 'demo@kbis.bf',
            'password': 'demo123',
            'first_name': 'Demo',
            'last_name': 'Utilisateur',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True,
            'groups': ['CONTROLE']
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # Supprimer l'utilisateur s'il existe déjà
            User.objects.filter(username=user_data['username']).delete()
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_staff=user_data['is_staff'],
                is_superuser=user_data['is_superuser'],
                is_active=user_data['is_active']
            )
            
            created_users.append(user)
            print(f"✅ Utilisateur créé: {user.username} ({user.email})")
            
            # Assigner les groupes
            if 'groups' in user_data:
                for group_name in user_data['groups']:
                    try:
                        group, created = Group.objects.get_or_create(name=group_name)
                        user.groups.add(group)
                        print(f"   📋 Groupe assigné: {group_name}")
                    except Exception as e:
                        print(f"   ❌ Erreur assignation groupe {group_name}: {e}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création de {user_data['username']}: {e}")
    
    return created_users

def create_production_config():
    """Crée la configuration d'entreprise en production"""
    print("🏢 Configuration de l'entreprise en production...")
    
    try:
        # Supprimer les configurations existantes
        ConfigurationEntreprise.objects.all().delete()
        
        # Créer la nouvelle configuration
        config = ConfigurationEntreprise.objects.create(
            nom_entreprise='KBIS IMMOBILIER',
            adresse='123 Rue de l\'Immobilier',
            ville='Ouagadougou',
            code_postal='01 BP 1234',
            telephone='+226 25 12 34 56',
            email='contact@kbis.bf',
            actif=True
        )
        
        print(f"✅ Configuration entreprise créée: {config.nom_entreprise}")
        return config
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la configuration: {e}")
        return None

def main():
    """Fonction principale"""
    print("🚀 Migration des utilisateurs vers la production...")
    print("=" * 60)
    
    # Créer la configuration d'entreprise
    config = create_production_config()
    
    # Créer les utilisateurs de test
    users = create_production_users()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES UTILISATEURS DE PRODUCTION")
    print("=" * 60)
    print("🔑 Identifiants de connexion:")
    print("   • admin / admin123 (Administrateur) - Groupes: ADMINISTRATION, PRIVILEGE")
    print("   • gestionnaire / gestion123 (Gestionnaire) - Groupe: ADMINISTRATION")
    print("   • agent / agent123 (Agent) - Groupe: PRIVILEGE")
    print("   • comptable / comptable123 (Comptable) - Groupe: CAISSE")
    print("   • demo / demo123 (Démo) - Groupe: CONTROLE")
    print("\n🌐 URL de connexion: https://appli-kbis-1.onrender.com/utilisateurs/connexion-groupes/")
    print("=" * 60)

if __name__ == '__main__':
    main()
