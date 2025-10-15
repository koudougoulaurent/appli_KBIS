#!/usr/bin/env python3
"""
Script de configuration initiale pour Render
"""
import os
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render_minimal')
django.setup()

def create_superuser():
    """Créer le superutilisateur"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='System'
            )
            print("OK Superutilisateur cree: admin/admin123")
        else:
            print("INFO Superutilisateur existe deja")
    except Exception as e:
        print(f"ERREUR creation superutilisateur: {e}")

def create_groups():
    """Créer les groupes de travail"""
    try:
        from django.contrib.auth.models import Group
        
        groups = [
            {'name': 'PRIVILEGE', 'permissions': []},
            {'name': 'MANAGER', 'permissions': []},
            {'name': 'AGENT', 'permissions': []},
            {'name': 'TENANT', 'permissions': []},
        ]
        
        for group_data in groups:
            group, created = Group.objects.get_or_create(name=group_data['name'])
            if created:
                print(f"OK Groupe cree: {group_data['name']}")
            else:
                print(f"INFO Groupe existe deja: {group_data['name']}")
                
    except Exception as e:
        print(f"ERREUR creation groupes: {e}")

def setup_database():
    """Configuration complète de la base de données"""
    try:
        print("Configuration de la base de donnees...")
        
        # Synchroniser la base de données
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
        print("OK Base de donnees synchronisee")
        
        # Créer les groupes
        create_groups()
        
        # Créer le superutilisateur
        create_superuser()
        
        print("Configuration terminee avec succes!")
        
    except Exception as e:
        print(f"ERREUR configuration: {e}")

if __name__ == "__main__":
    setup_database()
