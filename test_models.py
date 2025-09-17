#!/usr/bin/env python
"""
Script pour tester les modèles et identifier les erreurs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
    print("✅ Django configuré avec succès")
    
    from utilisateurs.models import GroupeTravail, Utilisateur
    print("✅ Modèles importés avec succès")
    
    # Tester la création d'un groupe
    groupe, created = GroupeTravail.objects.get_or_create(
        nom='TEST',
        defaults={
            'description': 'Groupe de test',
            'permissions': {'modules': ['test']},
            'actif': True
        }
    )
    print(f"✅ GroupeTravail créé: {groupe}")
    
    # Tester la création d'un utilisateur
    user, created = Utilisateur.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@test.com',
            'password': 'test123',
            'groupe_travail': groupe
        }
    )
    print(f"✅ Utilisateur créé: {user}")
    
    print("🎉 Tous les tests passent !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
