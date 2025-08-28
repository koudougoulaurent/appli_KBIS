#!/usr/bin/env python
"""
Script pour initialiser la base de données et créer un superutilisateur par défaut
"""

import os
import django
from django.core.management import execute_from_command_line

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

# Importation des modules Django nécessaires
from django.core.management import call_command
from django.contrib.auth import get_user_model

def init_database():
    """Initialise la base de données"""
    print("Initialisation de la base de données...")
    try:
        # Exécuter les migrations
        call_command('migrate')
        print("Base de données initialisée avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")

def create_superuser():
    """Crée un superutilisateur par défaut"""
    print("Création du superutilisateur...")
    try:
        User = get_user_model()
        
        # Vérifier si le superutilisateur existe déjà
        if not User.objects.filter(username='admin').exists():
            # Créer le superutilisateur
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print("Superutilisateur 'admin' créé avec succès!")
            print("Identifiants par défaut:")
            print("  Nom d'utilisateur: admin")
            print("  Mot de passe: admin123")
            print("  Email: admin@example.com")
            print("IMPORTANT: Changez le mot de passe après la première connexion!")
        else:
            print("Le superutilisateur 'admin' existe déjà.")
    except Exception as e:
        print(f"Erreur lors de la création du superutilisateur: {e}")

def collect_static():
    """Collecte les fichiers statiques"""
    print("Collecte des fichiers statiques...")
    try:
        call_command('collectstatic', interactive=False)
        print("Fichiers statiques collectés avec succès!")
    except Exception as e:
        print(f"Erreur lors de la collecte des fichiers statiques: {e}")

if __name__ == '__main__':
    print("Script d'initialisation de l'application de gestion immobilière")
    print("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Créer le superutilisateur
    create_superuser()
    
    # Collecter les fichiers statiques
    collect_static()
    
    print("=" * 60)
    print("Initialisation terminée!")
    print("Vous pouvez maintenant démarrer l'application avec start.bat ou start.sh")