#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test
Utilisez ce script pour ajouter des utilisateurs de test à la base de données
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
from core.models import ConfigurationEntreprise

User = get_user_model()

def create_test_users():
    """Crée des utilisateurs de test"""
    print("👥 Création des utilisateurs de test...")
    
    # Utilisateurs de test
    test_users = [
        {
            'username': 'admin',
            'email': 'admin@kbis.bf',
            'password': 'admin123',
            'first_name': 'Administrateur',
            'last_name': 'Système',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        },
        {
            'username': 'gestionnaire',
            'email': 'gestionnaire@kbis.bf',
            'password': 'gestion123',
            'first_name': 'Jean',
            'last_name': 'Gestionnaire',
            'is_staff': True,
            'is_superuser': False,
            'is_active': True
        },
        {
            'username': 'agent',
            'email': 'agent@kbis.bf',
            'password': 'agent123',
            'first_name': 'Marie',
            'last_name': 'Agent',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True
        },
        {
            'username': 'comptable',
            'email': 'comptable@kbis.bf',
            'password': 'comptable123',
            'first_name': 'Paul',
            'last_name': 'Comptable',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True
        },
        {
            'username': 'demo',
            'email': 'demo@kbis.bf',
            'password': 'demo123',
            'first_name': 'Demo',
            'last_name': 'Utilisateur',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # Vérifier si l'utilisateur existe déjà
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                    'is_active': user_data['is_active']
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                created_users.append(user)
                print(f"✅ Utilisateur créé: {user.username} ({user.email})")
            else:
                print(f"ℹ️ Utilisateur existe déjà: {user.username}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création de {user_data['username']}: {e}")
    
    return created_users

def create_entreprise_config():
    """Crée la configuration d'entreprise"""
    print("🏢 Configuration de l'entreprise...")
    
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
    print("🚀 Création des utilisateurs de test et configuration...")
    print("=" * 60)
    
    # Créer la configuration d'entreprise
    config = create_entreprise_config()
    
    # Créer les utilisateurs de test
    users = create_test_users()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES UTILISATEURS DE TEST")
    print("=" * 60)
    print("🔑 Identifiants de connexion:")
    print("   • admin / admin123 (Administrateur)")
    print("   • gestionnaire / gestion123 (Gestionnaire)")
    print("   • agent / agent123 (Agent)")
    print("   • comptable / comptable123 (Comptable)")
    print("   • demo / demo123 (Démo)")
    print("\n🌐 URL de connexion: https://appli-kbis.onrender.com/utilisateurs/connexion-groupes/")
    print("=" * 60)

if __name__ == '__main__':
    main()