#!/usr/bin/env python
"""
Script d'initialisation des données pour Render
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from proprietes.models import TypeBien
from core.models import ConfigurationEntreprise

User = get_user_model()

def init_data():
    """Initialiser les données de base"""
    print("🚀 Initialisation des données...")
    
    # Créer les groupes
    groups = ['ADMINISTRATION', 'PRIVILEGE', 'CAISSE', 'CONTROLES']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"✅ Groupe créé: {group_name}")
        else:
            print(f"ℹ️ Groupe existant: {group_name}")
    
    # Créer les types de biens
    types_bien = [
        'Appartement', 'Maison', 'Studio', 'Loft', 'Villa', 'Duplex',
        'Penthouse', 'Château', 'Ferme', 'Bureau', 'Commerce',
        'Entrepôt', 'Garage', 'Terrain', 'Autre'
    ]
    
    for type_name in types_bien:
        type_bien, created = TypeBien.objects.get_or_create(nom=type_name)
        if created:
            print(f"✅ Type créé: {type_name}")
        else:
            print(f"ℹ️ Type existant: {type_name}")
    
    # Créer les utilisateurs de test
    test_users = [
        {'username': 'admin', 'email': 'admin@example.com', 'password': 'admin123', 'groups': ['ADMINISTRATION']},
        {'username': 'caisse1', 'email': 'caisse1@example.com', 'password': 'caisse123', 'groups': ['CAISSE']},
        {'username': 'controle1', 'email': 'controle1@example.com', 'password': 'controle123', 'groups': ['CONTROLES']},
        {'username': 'admin1', 'email': 'admin1@example.com', 'password': 'admin123', 'groups': ['ADMINISTRATION']},
        {'username': 'privilege1', 'email': 'privilege1@example.com', 'password': 'privilege123', 'groups': ['PRIVILEGE']},
    ]
    
    for user_data in test_users:
        username = user_data['username']
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=user_data['password']
            )
            # Ajouter aux groupes
            for group_name in user_data['groups']:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            print(f"✅ Utilisateur créé: {username}")
        else:
            print(f"ℹ️ Utilisateur existant: {username}")
    
    # Configuration entreprise
    config, created = ConfigurationEntreprise.objects.get_or_create(
        nom_entreprise="Gestion Immobilière KBIS",
        adresse="123 Rue de l'Immobilier",
        ville="Ouagadougou",
        code_postal="01 BP 1234",
        telephone="+226 25 12 34 56",
        email="contact@kbis.bf"
    )
    
    if created:
        print("✅ Configuration entreprise créée")
    else:
        print("ℹ️ Configuration entreprise existante")
    
    print("🎉 Initialisation terminée avec succès !")

if __name__ == "__main__":
    init_data()