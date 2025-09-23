#!/usr/bin/env python3
"""
Script de lancement final de l'application Django
Résout définitivement le problème de la variable d'environnement DJANGO_SETTINGS_MODULE
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Lance l'application Django avec la configuration correcte"""
    
    # Définir la variable d'environnement
    os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings'
    
    # Ajouter le répertoire courant au path Python
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    print("🚀 Lancement de l'application Django...")
    print("📍 URL: http://127.0.0.1:8000/")
    print("🛑 Arrêter avec Ctrl+C")
    print("=" * 50)
    
    try:
        # Lancer le serveur Django
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'runserver', '8000'])
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        print("🔧 Solutions possibles:")
        print("1. Vérifiez que tous les modules sont installés")
        print("2. Vérifiez la configuration Django")
        print("3. Redémarrez l'application")

if __name__ == "__main__":
    main()
