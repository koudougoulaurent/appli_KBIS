#!/usr/bin/env python
"""
Script de diagnostic pour l'erreur 500
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

from django.db import connection
from django.core.management import call_command

def main():
    """Diagnostic de l'erreur 500"""
    print("DIAGNOSTIC DE L'ERREUR 500")
    print("=" * 50)
    
    try:
        # Test de connexion à la base de données
        print("1. Test de connexion à la base de données...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("   OK: Connexion à la base de données réussie")
        
        # Vérification des migrations
        print("\n2. Vérification des migrations...")
        try:
            call_command('showmigrations', '--plan', verbosity=0)
            print("   OK: Migrations vérifiées")
        except Exception as e:
            print(f"   ERREUR: {e}")
        
        # Test des modèles
        print("\n3. Test des modèles...")
        try:
            from proprietes.models import Locataire, Bailleur
            print("   OK: Modèles importés avec succès")
            
            # Test de création d'un objet (sans sauvegarder)
            locataire = Locataire(
                nom="Test",
                prenom="Test",
                telephone="0123456789",
                email="test@test.com"
            )
            print("   OK: Création d'objet Locataire réussie")
            
        except Exception as e:
            print(f"   ERREUR: {e}")
        
        # Vérification des settings
        print("\n4. Vérification des settings...")
        from django.conf import settings
        print(f"   DEBUG: {settings.DEBUG}")
        print(f"   DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
        print(f"   INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
        
        print("\nDIAGNOSTIC TERMINE")
        
    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

