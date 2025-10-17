#!/usr/bin/env python
"""
Script de diagnostic pour identifier le problème d'import 'packages'
"""
import os
import sys

# Ajouter le répertoire du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test les imports un par un"""
    print("DIAGNOSTIC DES IMPORTS")
    print("=" * 40)
    
    try:
        print("1. Test Django...")
        import django
        print("   OK Django importe")
    except Exception as e:
        print(f"   ERREUR Django: {e}")
        return
    
    try:
        print("2. Test settings...")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
        from django.conf import settings
        print("   OK Settings importes")
    except Exception as e:
        print(f"   ERREUR settings: {e}")
        return
    
    try:
        print("3. Test applications...")
        apps = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications']
        for app in apps:
            try:
                module = __import__(app)
                print(f"   OK {app}")
            except Exception as e:
                print(f"   ERREUR {app}: {e}")
    except Exception as e:
        print(f"   ERREUR applications: {e}")
    
    try:
        print("4. Test modeles core...")
        from core.models import ConfigurationEntreprise
        print("   OK ConfigurationEntreprise")
    except Exception as e:
        print(f"   ERREUR ConfigurationEntreprise: {e}")
    
    try:
        print("5. Test modeles utilisateurs...")
        from utilisateurs.models import Utilisateur
        print("   OK Utilisateur")
    except Exception as e:
        print(f"   ERREUR Utilisateur: {e}")

if __name__ == '__main__':
    test_imports()
