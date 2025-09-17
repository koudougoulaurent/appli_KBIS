#!/usr/bin/env python
"""
Script pour créer les utilisateurs de test avec le bon modèle
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import TypeBien

def create_test_users():
    """Crée les utilisateurs de test"""
    print("🚀 Création des utilisateurs de test...")
    
    # Créer les groupes de travail
    groupes_data = [
        {'nom': 'PRIVILEGE', 'description': 'Groupe avec tous les privilèges'},
        {'nom': 'ADMINISTRATION', 'description': 'Groupe d\'administration'},
        {'nom': 'CAISSE', 'description': 'Groupe de gestion de la caisse'},
        {'nom': 'CONTROLES', 'description': 'Groupe de contrôles'},
    ]
    
    for groupe_data in groupes_data:
        groupe, created = GroupeTravail.objects.get_or_create(
            nom=groupe_data['nom'],
            defaults={'description': groupe_data['description'], 'actif': True}
        )
        if created:
            print(f"✅ Groupe {groupe.nom} créé")
        else:
            print(f"ℹ️  Groupe {groupe.nom} existe déjà")
    
    # Créer les types de biens
    types_bien = [
        'Appartement', 'Maison', 'Studio', 'Loft', 'Villa', 'Duplex',
        'Penthouse', 'Château', 'Ferme', 'Bureau', 'Commerce', 'Entrepôt',
        'Garage', 'Terrain', 'Autre'
    ]
    
    for type_nom in types_bien:
        type_bien, created = TypeBien.objects.get_or_create(
            nom=type_nom,
            defaults={'actif': True}
        )
        if created:
            print(f"✅ Type {type_nom} créé")
        else:
            print(f"ℹ️  Type {type_nom} existe déjà")
    
    # Créer les utilisateurs de test
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@gestimmob.com',
            'password': 'admin123',
            'first_name': 'Administrateur',
            'last_name': 'Principal',
            'groupe': 'PRIVILEGE'
        },
        {
            'username': 'caisse1',
            'email': 'caisse@gestimmob.com',
            'password': 'caisse123',
            'first_name': 'Caissier',
            'last_name': 'Principal',
            'groupe': 'CAISSE'
        },
        {
            'username': 'controle1',
            'email': 'controle@gestimmob.com',
            'password': 'controle123',
            'first_name': 'Contrôleur',
            'last_name': 'Principal',
            'groupe': 'CONTROLES'
        },
        {
            'username': 'admin1',
            'email': 'admin1@gestimmob.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'Immobilier',
            'groupe': 'ADMINISTRATION'
        },
        {
            'username': 'privilege1',
            'email': 'privilege@gestimmob.com',
            'password': 'privilege123',
            'first_name': 'Privilège',
            'last_name': 'Test',
            'groupe': 'PRIVILEGE'
        }
    ]
    
    for user_data in users_data:
        # Supprimer l'ancien utilisateur s'il existe
        Utilisateur.objects.filter(username=user_data['username']).delete()
        
        # Créer le nouvel utilisateur
        user = Utilisateur.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        
        # Assigner au groupe
        groupe = GroupeTravail.objects.get(nom=user_data['groupe'])
        user.groupe_travail = groupe
        user.save()
        
        print(f"✅ Utilisateur {user.username} créé (Groupe: {groupe.nom})")
    
    print("🎉 Tous les utilisateurs de test ont été créés avec succès!")
    print("\n📋 Informations de connexion:")
    print("=" * 50)
    for user_data in users_data:
        print(f"👤 {user_data['username']} / {user_data['password']} (Groupe: {user_data['groupe']})")
    print("=" * 50)

if __name__ == "__main__":
    create_test_users()
