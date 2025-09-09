#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test pour l'application GESTIMMOB
"""

import os
import sys
import django
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from django.contrib.auth import get_user_model

def create_groups():
    """Créer les groupes de travail s'ils n'existent pas"""
    print("🔧 Création des groupes de travail...")
    
    groups_data = [
        {
            'nom': 'CAISSE',
            'description': 'Groupe pour la gestion de la caisse et des paiements',
            'permissions': {
                'modules': ['paiements', 'retraits', 'recapitulatifs'],
                'actions': ['view', 'add', 'change', 'delete']
            }
        },
        {
            'nom': 'CONTROLES',
            'description': 'Groupe pour les contrôles et validations',
            'permissions': {
                'modules': ['paiements', 'contrats', 'proprietes'],
                'actions': ['view', 'change']
            }
        },
        {
            'nom': 'ADMINISTRATION',
            'description': 'Groupe pour l\'administration générale',
            'permissions': {
                'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'],
                'actions': ['view', 'add', 'change']
            }
        },
        {
            'nom': 'PRIVILEGE',
            'description': 'Groupe avec tous les privilèges',
            'permissions': {
                'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements', 'retraits', 'recapitulatifs'],
                'actions': ['view', 'add', 'change', 'delete']
            }
        }
    ]
    
    for group_data in groups_data:
        group, created = GroupeTravail.objects.get_or_create(
            nom=group_data['nom'],
            defaults=group_data
        )
        if created:
            print(f"   ✅ Groupe {group.nom} créé")
        else:
            print(f"   ℹ️  Groupe {group.nom} existe déjà")

def create_test_users():
    """Créer des utilisateurs de test"""
    print("\n👥 Création des utilisateurs de test...")
    
    # Récupérer les groupes
    groupe_caisse = GroupeTravail.objects.get(nom='CAISSE')
    groupe_controles = GroupeTravail.objects.get(nom='CONTROLES')
    groupe_admin = GroupeTravail.objects.get(nom='ADMINISTRATION')
    groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
    
    users_data = [
        # Superutilisateur
        {
            'username': 'admin',
            'email': 'admin@gestimmob.com',
            'password': 'admin123',
            'first_name': 'Administrateur',
            'last_name': 'Système',
            'is_staff': True,
            'is_superuser': True,
            'groupe_travail': groupe_privilege,
            'poste': 'Administrateur Système',
            'departement': 'IT',
            'telephone': '+225 07 12 34 56 78',
            'adresse': 'Abidjan, Côte d\'Ivoire'
        },
        # Groupe CAISSE
        {
            'username': 'caisse1',
            'email': 'caisse1@gestimmob.com',
            'password': 'caisse123',
            'first_name': 'Marie',
            'last_name': 'Kouassi',
            'groupe_travail': groupe_caisse,
            'poste': 'Agent de Caisse',
            'departement': 'Finance',
            'telephone': '+225 07 23 45 67 89',
            'adresse': 'Cocody, Abidjan'
        },
        {
            'username': 'caisse2',
            'email': 'caisse2@gestimmob.com',
            'password': 'caisse123',
            'first_name': 'Jean',
            'last_name': 'Traoré',
            'groupe_travail': groupe_caisse,
            'poste': 'Responsable Caisse',
            'departement': 'Finance',
            'telephone': '+225 07 34 56 78 90',
            'adresse': 'Plateau, Abidjan'
        },
        # Groupe CONTROLES
        {
            'username': 'controle1',
            'email': 'controle1@gestimmob.com',
            'password': 'controle123',
            'first_name': 'Fatou',
            'last_name': 'Diabaté',
            'groupe_travail': groupe_controles,
            'poste': 'Contrôleur',
            'departement': 'Contrôle',
            'telephone': '+225 07 45 67 89 01',
            'adresse': 'Yopougon, Abidjan'
        },
        {
            'username': 'controle2',
            'email': 'controle2@gestimmob.com',
            'password': 'controle123',
            'first_name': 'Kouassi',
            'last_name': 'Koné',
            'groupe_travail': groupe_controles,
            'poste': 'Superviseur Contrôle',
            'departement': 'Contrôle',
            'telephone': '+225 07 56 78 90 12',
            'adresse': 'Marcory, Abidjan'
        },
        # Groupe ADMINISTRATION
        {
            'username': 'admin1',
            'email': 'admin1@gestimmob.com',
            'password': 'admin123',
            'first_name': 'Aminata',
            'last_name': 'Sangaré',
            'groupe_travail': groupe_admin,
            'poste': 'Gestionnaire',
            'departement': 'Administration',
            'telephone': '+225 07 67 89 01 23',
            'adresse': 'Riviera, Abidjan'
        },
        {
            'username': 'admin2',
            'email': 'admin2@gestimmob.com',
            'password': 'admin123',
            'first_name': 'Moussa',
            'last_name': 'Ouattara',
            'groupe_travail': groupe_admin,
            'poste': 'Chef Administration',
            'departement': 'Administration',
            'telephone': '+225 07 78 90 12 34',
            'adresse': 'Angré, Abidjan'
        },
        # Groupe PRIVILEGE
        {
            'username': 'privilege1',
            'email': 'privilege1@gestimmob.com',
            'password': 'privilege123',
            'first_name': 'Kadiatou',
            'last_name': 'Coulibaly',
            'groupe_travail': groupe_privilege,
            'poste': 'Directeur',
            'departement': 'Direction',
            'telephone': '+225 07 89 01 23 45',
            'adresse': 'Zone 4, Abidjan'
        },
        {
            'username': 'privilege2',
            'email': 'privilege2@gestimmob.com',
            'password': 'privilege123',
            'first_name': 'Ibrahim',
            'last_name': 'Bamba',
            'groupe_travail': groupe_privilege,
            'poste': 'Directeur Adjoint',
            'departement': 'Direction',
            'telephone': '+225 07 90 12 34 56',
            'adresse': 'Bingerville, Abidjan'
        }
    ]
    
    for user_data in users_data:
        username = user_data['username']
        password = user_data.pop('password')
        
        user, created = Utilisateur.objects.get_or_create(
            username=username,
            defaults=user_data
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"   ✅ Utilisateur {username} créé ({user.get_nom_complet()})")
        else:
            print(f"   ℹ️  Utilisateur {username} existe déjà")

def display_users():
    """Afficher la liste des utilisateurs créés"""
    print("\n📋 Liste des utilisateurs de test :")
    print("=" * 80)
    
    for group in GroupeTravail.objects.all():
        print(f"\n🔹 Groupe {group.nom}:")
        users = Utilisateur.objects.filter(groupe_travail=group)
        for user in users:
            print(f"   • {user.username} - {user.get_nom_complet()}")
            print(f"     Email: {user.email}")
            print(f"     Poste: {user.poste}")
            print(f"     Téléphone: {user.telephone}")
            print()

def main():
    """Fonction principale"""
    print("🚀 Création des utilisateurs de test pour GESTIMMOB")
    print("=" * 60)
    
    try:
        # Créer les groupes
        create_groups()
        
        # Créer les utilisateurs
        create_test_users()
        
        # Afficher la liste
        display_users()
        
        print("\n✅ Création terminée avec succès !")
        print("\n🔑 Informations de connexion :")
        print("   • Superutilisateur: admin / admin123")
        print("   • Caisse: caisse1 / caisse123")
        print("   • Contrôle: controle1 / controle123")
        print("   • Administration: admin1 / admin123")
        print("   • Privilège: privilege1 / privilege123")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création : {e}")
        return False
    
    return True

if __name__ == '__main__':
    main()
