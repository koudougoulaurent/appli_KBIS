#!/usr/bin/env python
"""
Script de lancement simple pour l'application Django
Contourne le problème 'packages' en utilisant une configuration minimale
"""
import os
import sys
import django
from pathlib import Path

# Configuration de l'environnement
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("🚀 Lancement de l'application Django...")
    print("📍 URL: http://127.0.0.1:8000/")
    print("🛑 Arrêter avec Ctrl+C")
    print("-" * 50)
    
    # Configuration Django
    django.setup()
    
    # Import des modules nécessaires
    from django.core.management import execute_from_command_line
    from django.core.wsgi import get_wsgi_application
    
    # Lancer le serveur
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
    
except Exception as e:
    print(f"❌ Erreur lors du lancement: {e}")
    print("\n🔧 Solutions possibles:")
    print("1. Vérifiez que tous les modules sont installés")
    print("2. Vérifiez la configuration Django")
    print("3. Redémarrez l'application")
    
    # Essayer de lancer quand même
    try:
        print("\n🔄 Tentative de lancement direct...")
        os.system("python manage.py runserver 127.0.0.1:8000")
    except:
        print("❌ Impossible de lancer l'application")
