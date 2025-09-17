#!/usr/bin/env python
"""
Script simple pour créer un utilisateur PRIVILEGE
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail

User = get_user_model()

def create_privilege_user():
    print("🔧 Création d'un utilisateur PRIVILEGE...")
    
    try:
        # 1. Créer ou récupérer le groupe PRIVILEGE
        groupe, created = GroupeTravail.objects.get_or_create(
            nom='PRIVILEGE',
            defaults={
                'description': 'Groupe Privilège',
                'permissions': {'modules': ['all'], 'actions': ['all']},
                'actif': True
            }
        )
        print(f"✅ Groupe PRIVILEGE: {'créé' if created else 'existe déjà'}")
        
        # 2. Supprimer l'ancien utilisateur privilege1 s'il existe
        try:
            old_user = User.objects.get(username='privilege1')
            old_user.delete()
            print("🗑️ Ancien utilisateur privilege1 supprimé")
        except User.DoesNotExist:
            print("ℹ️ Aucun ancien utilisateur privilege1 trouvé")
        
        # 3. Créer le nouvel utilisateur PRIVILEGE
        user = User.objects.create_user(
            username='privilege1',
            password='privilege123',
            email='privilege1@test.com',
            first_name='Privilege',
            last_name='User',
            actif=True
        )
        user.is_superuser = True
        user.is_staff = True
        user.groupe_travail = groupe
        user.save()
        print("✅ Utilisateur privilege1 créé avec succès")
        
        # 4. Test de connexion
        from django.contrib.auth import authenticate
        test_user = authenticate(username='privilege1', password='privilege123')
        if test_user:
            print("✅ Test de connexion réussi")
            print("🎉 UTILISATEUR PRIVILEGE CRÉÉ AVEC SUCCÈS !")
            print("📋 Identifiants : privilege1 / privilege123")
        else:
            print("❌ Test de connexion échoué")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_privilege_user()