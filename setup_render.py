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
        from utilisateurs.models import GroupeTravail
        
        groups = [
            {
                'nom': 'ADMINISTRATION', 
                'description': 'Gestion administrative',
                'permissions': {'modules': ['proprietes', 'contrats', 'utilisateurs']},
                'actif': True
            },
            {
                'nom': 'CAISSE', 
                'description': 'Gestion des paiements et retraits',
                'permissions': {'modules': ['paiements', 'retraits']},
                'actif': True
            },
            {
                'nom': 'CONTROLES', 
                'description': 'Contrôle et audit',
                'permissions': {'modules': ['rapports', 'audit']},
                'actif': True
            },
            {
                'nom': 'PRIVILEGE', 
                'description': 'Accès complet',
                'permissions': {'modules': ['paiements', 'retraits', 'proprietes', 'contrats', 'utilisateurs', 'rapports', 'audit']},
                'actif': True
            },
        ]
        
        for group_data in groups:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=group_data['nom'],
                defaults={
                    'description': group_data['description'],
                    'permissions': group_data['permissions'],
                    'actif': group_data['actif']
                }
            )
            if created:
                print(f"OK GroupeTravail cree: {group_data['nom']}")
            else:
                print(f"INFO GroupeTravail existe deja: {group_data['nom']}")
                
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
