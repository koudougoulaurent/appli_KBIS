#!/usr/bin/env python
"""
Script de lancement du serveur Django
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
    # Configuration Django
    django.setup()
    
    # Import des modules nécessaires
    from django.core.management import execute_from_command_line
    from django.core.wsgi import get_wsgi_application
    
    print("🚀 Lancement du serveur Django...")
    print("📍 URL: http://127.0.0.1:8000/")
    print("🛑 Arrêter avec Ctrl+C")
    print("-" * 50)
    
    # Lancer le serveur
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
    
except Exception as e:
    print(f"❌ Erreur lors du lancement: {e}")
    print("\n🔧 Solutions possibles:")
    print("1. Vérifiez que tous les modules sont installés")
    print("2. Vérifiez la configuration Django")
    print("3. Essayez: python manage.py runserver")
