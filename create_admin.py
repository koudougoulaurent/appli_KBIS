#!/usr/bin/env python
"""
Script pour créer un superutilisateur admin
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from django.contrib.auth.hashers import make_password

def create_admin():
    """Créer un superutilisateur admin"""
    print('=== Création du superutilisateur admin ===')
    
    # Créer le groupe PRIVILEGE s'il n'existe pas
    groupe, created = GroupeTravail.objects.get_or_create(
        nom='PRIVILEGE',
        defaults={'description': 'Groupe privilégié avec tous les droits'}
    )
    print(f'Groupe PRIVILEGE: {"créé" if created else "existant"}')
    
    # Créer le superutilisateur
    user, created = Utilisateur.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@test.com',
            'password': make_password('admin123'),
            'is_staff': True,
            'is_superuser': True,
            'groupe_travail': groupe
        }
    )
    
    if created:
        print('✅ Superutilisateur admin créé avec succès!')
        print('   Nom d\'utilisateur: admin')
        print('   Mot de passe: admin123')
        print('   Groupe: PRIVILEGE')
    else:
        print('ℹ️  Superutilisateur admin existe déjà')
        # Mettre à jour le groupe si nécessaire
        if not user.groupe_travail:
            user.groupe_travail = groupe
            user.save()
            print('   Groupe PRIVILEGE assigné')
    
    print('=== Terminé ===')

if __name__ == '__main__':
    create_admin()
