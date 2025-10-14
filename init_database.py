#!/usr/bin/env python
"""
Script pour initialiser la base de données sur Render
"""
import os
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

def init_database():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données...")
    
    try:
        # Créer les migrations pour les apps principales
        print("📋 Création des migrations...")
        execute_from_command_line(['manage.py', 'makemigrations', 'utilisateurs'])
        execute_from_command_line(['manage.py', 'makemigrations', 'proprietes'])
        execute_from_command_line(['manage.py', 'makemigrations', 'contrats'])
        execute_from_command_line(['manage.py', 'makemigrations', 'paiements'])
        execute_from_command_line(['manage.py', 'makemigrations', 'notifications'])
        
        # Appliquer les migrations
        print("🚀 Application des migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        
        # Créer un superutilisateur par défaut
        print("👤 Création du superutilisateur...")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@kbis.com',
                password='admin123'
            )
            print("✅ Superutilisateur créé: admin/admin123")
        else:
            print("ℹ️ Superutilisateur existe déjà")
        
        print("✅ Base de données initialisée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == '__main__':
    init_database()
