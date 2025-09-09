#!/usr/bin/env python
"""
Script pour corriger l'utilisateur privilege1 avec le bon hachage de mot de passe Django
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from utilisateurs.models import Utilisateur, GroupeTravail

def fix_privilege_user():
    """Corriger l'utilisateur privilege1 avec le bon hachage de mot de passe"""
    
    print("🔧 Correction de l'utilisateur privilege1")
    print("=" * 50)
    
    try:
        # Récupérer ou créer le groupe PRIVILEGE
        groupe, created = GroupeTravail.objects.get_or_create(
            nom='PRIVILEGE',
            defaults={
                'description': 'Groupe avec tous les privilèges',
                'permissions': {
                    "modules": ["utilisateurs", "proprietes", "contrats", "paiements", "retraits", "recapitulatifs"],
                    "actions": ["view", "add", "change", "delete"]
                },
                'actif': True
            }
        )
        
        if created:
            print("✅ Groupe PRIVILEGE créé")
        else:
            print("✅ Groupe PRIVILEGE trouvé")
        
        # Récupérer ou créer l'utilisateur privilege1
        user, created = Utilisateur.objects.get_or_create(
            username='privilege1',
            defaults={
                'email': 'privilege1@gestimmob.com',
                'first_name': 'Kadiatou',
                'last_name': 'Coulibaly',
                'poste': 'Directeur',
                'departement': 'Direction',
                'telephone': '+225 07 89 01 23 45',
                'adresse': 'Zone 4, Abidjan',
                'groupe_travail': groupe,
                'is_active': True,
                'actif': True
            }
        )
        
        # Mettre à jour le mot de passe avec le bon hachage Django
        user.set_password('test123')
        user.groupe_travail = groupe
        user.is_active = True
        user.actif = True
        user.save()
        
        if created:
            print("✅ Utilisateur privilege1 créé")
        else:
            print("✅ Utilisateur privilege1 mis à jour")
        
        # Vérifier la connexion
        print("\n🔍 Vérification de la connexion...")
        
        # Test de connexion
        from django.contrib.auth import authenticate
        
        auth_user = authenticate(username='privilege1', password='test123')
        
        if auth_user:
            print("✅ Authentification réussie !")
            print(f"   • Utilisateur: {auth_user.username}")
            print(f"   • Nom complet: {auth_user.get_full_name()}")
            print(f"   • Email: {auth_user.email}")
            print(f"   • Groupe: {auth_user.groupe_travail.nom if auth_user.groupe_travail else 'Aucun'}")
            print(f"   • Actif: {auth_user.is_active}")
            print(f"   • Staff: {auth_user.is_staff}")
            print(f"   • Superuser: {auth_user.is_superuser}")
        else:
            print("❌ Échec de l'authentification")
            
            # Debug: vérifier les détails de l'utilisateur
            print("\n🔍 Détails de l'utilisateur en base :")
            user_db = Utilisateur.objects.get(username='privilege1')
            print(f"   • Username: {user_db.username}")
            print(f"   • Password hash: {user_db.password[:50]}...")
            print(f"   • Is active: {user_db.is_active}")
            print(f"   • Actif: {user_db.actif}")
            print(f"   • Groupe: {user_db.groupe_travail.nom if user_db.groupe_travail else 'Aucun'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fix_privilege_user()
