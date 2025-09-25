#!/usr/bin/env python
"""
Script pour migrer les données de SQLite vers PostgreSQL
Utilisez ce script après avoir configuré PostgreSQL sur Render
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from core.models import ConfigurationEntreprise

def migrate_to_postgresql():
    """Migre les données vers PostgreSQL"""
    print("🔄 Migration vers PostgreSQL...")
    
    try:
        # Vérifier la connexion PostgreSQL
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Connexion PostgreSQL établie")
        
        # Appliquer les migrations
        print("📦 Application des migrations...")
        call_command('migrate', verbosity=2)
        
        # Créer la configuration d'entreprise
        print("🏢 Configuration de l'entreprise...")
        ConfigurationEntreprise.objects.all().delete()
        
        config = ConfigurationEntreprise.objects.create(
            nom_entreprise='KBIS IMMOBILIER',
            adresse='123 Rue de l\'Immobilier',
            ville='Ouagadougou',
            code_postal='01 BP 1234',
            telephone='+226 25 12 34 56',
            email='contact@kbis.bf',
            actif=True
        )
        
        print("✅ Configuration entreprise créée:")
        print(f"   - Nom: {config.nom_entreprise}")
        print(f"   - Email: {config.email}")
        print(f"   - Téléphone: {config.telephone}")
        
        print("🎉 Migration terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    return True

if __name__ == '__main__':
    migrate_to_postgresql()