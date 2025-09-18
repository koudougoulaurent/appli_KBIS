#!/usr/bin/env python
"""
Script simple pour créer un superutilisateur admin
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from django.contrib.auth.hashers import make_password

# Créer le groupe PRIVILEGE
groupe, created = GroupeTravail.objects.get_or_create(
    nom='PRIVILEGE',
    defaults={'description': 'Groupe privilegie avec tous les droits'}
)
print('Groupe PRIVILEGE cree')

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
    print('Superutilisateur admin cree avec succes!')
    print('Nom d utilisateur: admin')
    print('Mot de passe: admin123')
else:
    print('Superutilisateur admin existe deja')
    if not user.groupe_travail:
        user.groupe_travail = groupe
        user.save()
        print('Groupe PRIVILEGE assigne')
