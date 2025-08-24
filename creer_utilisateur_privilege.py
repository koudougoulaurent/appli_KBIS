#!/usr/bin/env python
"""
Script pour créer un utilisateur de test du groupe PRIVILEGE
Usage: python creer_utilisateur_privilege.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail, Utilisateur

def creer_groupe_privilege():
    """Crée le groupe PRIVILEGE s'il n'existe pas"""
    groupe, created = GroupeTravail.objects.get_or_create(
        nom='PRIVILEGE',
        defaults={
            'description': 'Groupe avec privilèges étendus pour la gestion complète du système',
            'permissions': {
                'modules': [
                    'proprietes',
                    'contrats', 
                    'paiements',
                    'utilisateurs',
                    'notifications',
                    'core'
                ],
                'actions_speciales': [
                    'suppression_complete',
                    'gestion_profils',
                    'acces_toutes_donnees',
                    'modification_systeme'
                ]
            },
            'actif': True
        }
    )
    
    if created:
        print(f"✅ Groupe PRIVILEGE créé avec succès")
    else:
        print(f"ℹ️  Groupe PRIVILEGE existe déjà")
    
    return groupe

def creer_utilisateur_privilege():
    """Crée un utilisateur de test du groupe PRIVILEGE"""
    # Créer le groupe d'abord
    groupe_privilege = creer_groupe_privilege()
    
    # Vérifier si l'utilisateur existe déjà
    username = 'privilege1'
    try:
        utilisateur_existant = Utilisateur.objects.get(username=username)
        print(f"ℹ️  L'utilisateur {username} existe déjà")
        
        # Mettre à jour le groupe si nécessaire
        if utilisateur_existant.groupe_travail != groupe_privilege:
            utilisateur_existant.groupe_travail = groupe_privilege
            utilisateur_existant.save()
            print(f"✅ Groupe mis à jour pour l'utilisateur {username}")
        
        # Mettre à jour le mot de passe
        utilisateur_existant.set_password('test123')
        utilisateur_existant.save()
        print(f"✅ Mot de passe mis à jour pour l'utilisateur {username}")
        
        return utilisateur_existant
        
    except Utilisateur.DoesNotExist:
        pass
    
    # Créer le nouvel utilisateur
    try:
        utilisateur = Utilisateur.objects.create_user(
            username=username,
            email='privilege1@gestionimmo.com',
            password='test123',
            first_name='Utilisateur',
            last_name='Privilege',
            is_staff=True,
            is_active=True,
            groupe_travail=groupe_privilege,
            poste='Utilisateur Test',
            departement='Test',
            telephone='+33123456789',
            adresse='123 Rue de Test, 75001 Paris'
        )
        
        print(f"✅ Utilisateur {username} créé avec succès dans le groupe PRIVILEGE")
        print(f"   Nom d'utilisateur: {username}")
        print(f"   Mot de passe: test123")
        print(f"   Email: {utilisateur.email}")
        print(f"   Groupe: {utilisateur.get_groupe_display()}")
        
        return utilisateur
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {str(e)}")
        return None

def verifier_permissions(utilisateur):
    """Vérifie les permissions de l'utilisateur"""
    print(f"\n🔐 Vérification des permissions pour {utilisateur.username}:")
    print(f"   Groupe: {utilisateur.get_groupe_display()}")
    print(f"   Est staff: {utilisateur.is_staff}")
    print(f"   Est actif: {utilisateur.is_active}")
    print(f"   Est utilisateur privilégié: {utilisateur.is_privilege_user()}")
    
    modules_accessibles = utilisateur.get_accessible_modules()
    print(f"   Modules accessibles: {', '.join(modules_accessibles)}")
    
    if utilisateur.can_manage_profiles():
        print(f"   ✅ Peut gérer les profils")
    else:
        print(f"   ❌ Ne peut pas gérer les profils")

def main():
    """Fonction principale"""
    print("🚀 Création d'un utilisateur de test du groupe PRIVILEGE")
    print("=" * 60)
    
    # Créer l'utilisateur
    utilisateur = creer_utilisateur_privilege()
    
    if utilisateur:
        # Vérifier les permissions
        verifier_permissions(utilisateur)
        
        print(f"\n🎉 Utilisateur créé avec succès!")
        print(f"   Vous pouvez maintenant vous connecter avec:")
        print(f"   - Nom d'utilisateur: {utilisateur.username}")
        print(f"   - Mot de passe: test123")
        print(f"   - Groupe: PRIVILEGE")
        
    else:
        print(f"\n❌ Échec de la création de l'utilisateur")
        sys.exit(1)

if __name__ == '__main__':
    main()
