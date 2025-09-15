#!/usr/bin/env python
"""
Script de déploiement avec création automatique d'utilisateurs de test.
À exécuter sur Render après chaque déploiement.
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def main():
    """Fonction principale de déploiement."""
    print("🚀 DÉPLOIEMENT AVEC UTILISATEURS DE TEST")
    print("=" * 50)
    
    try:
        # Vérifier la connexion à la base de données
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Connexion à la base de données OK")
        
        # Appliquer les migrations
        print("📦 Application des migrations...")
        call_command('migrate', verbosity=1)
        print("✅ Migrations appliquées")
        
        # Collecter les fichiers statiques
        print("📁 Collecte des fichiers statiques...")
        call_command('collectstatic', '--noinput', verbosity=1)
        print("✅ Fichiers statiques collectés")
        
        # Créer les utilisateurs de test
        print("👥 Création des utilisateurs de test...")
        call_command('create_test_users', '--force')
        print("✅ Utilisateurs de test créés")
        
        # Vérifier que l'application fonctionne
        print("🔍 Vérification de l'application...")
        from django.test import Client
        client = Client()
        response = client.get('/')
        if response.status_code in [200, 302]:
            print("✅ Application fonctionnelle")
        else:
            print(f"⚠️  Application répond avec le code {response.status_code}")
        
        print("\n🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!")
        print("=" * 50)
        print("🔐 UTILISATEURS DE TEST DISPONIBLES:")
        print("   admin / admin123 (PRIVILEGE)")
        print("   caisse / caisse123 (CAISSE)")
        print("   admin_immobilier / admin123 (ADMINISTRATION)")
        print("   controleur / controle123 (CONTROLES)")
        print("   test / test123 (CAISSE)")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ ERREUR LORS DU DÉPLOIEMENT: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
