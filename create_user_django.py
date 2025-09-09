#!/usr/bin/env python
"""
Script pour créer l'utilisateur privilege1 avec Django
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
except Exception as e:
    print(f"Erreur de configuration Django: {e}")
    sys.exit(1)

from django.contrib.auth.hashers import make_password
from utilisateurs.models import Utilisateur, GroupeTravail

def create_privilege_user():
    """Créer l'utilisateur privilege1 avec le bon hachage de mot de passe"""
    
    print("🔧 Création de l'utilisateur privilege1")
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
        
        # Supprimer l'ancien utilisateur s'il existe
        try:
            old_user = Utilisateur.objects.get(username='privilege1')
            old_user.delete()
            print("🗑️ Ancien utilisateur privilege1 supprimé")
        except Utilisateur.DoesNotExist:
            pass
        
        # Créer le nouvel utilisateur
        user = Utilisateur.objects.create_user(
            username='privilege1',
            email='privilege1@gestimmob.com',
            password='test123',
            first_name='Kadiatou',
            last_name='Coulibaly',
            poste='Directeur',
            departement='Direction',
            telephone='+225 07 89 01 23 45',
            adresse='Zone 4, Abidjan',
            groupe_travail=groupe,
            is_active=True,
            actif=True
        )
        
        print("✅ Utilisateur privilege1 créé")
        
        # Test de connexion
        print("\n🔍 Test de connexion...")
        from django.contrib.auth import authenticate
        
        auth_user = authenticate(username='privilege1', password='test123')
        
        if auth_user:
            print("✅ Authentification réussie !")
            print(f"   • Utilisateur: {auth_user.username}")
            print(f"   • Nom complet: {auth_user.get_full_name()}")
            print(f"   • Email: {auth_user.email}")
            print(f"   • Groupe: {auth_user.groupe_travail.nom if auth_user.groupe_travail else 'Aucun'}")
            print(f"   • Actif: {auth_user.is_active}")
        else:
            print("❌ Échec de l'authentification")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    create_privilege_user()
