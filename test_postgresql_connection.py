#!/usr/bin/env python
"""
Script pour tester la connexion PostgreSQL sur Render
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

from django.db import connections
from django.core.management import call_command
from core.models import ConfigurationEntreprise

def test_postgresql_connection():
    """Teste la connexion PostgreSQL"""
    print("🔍 Test de connexion PostgreSQL...")
    
    try:
        # Test de connexion
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connexion PostgreSQL réussie!")
            print(f"📊 Version: {version}")
            
            # Vérifier les tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"📋 Tables disponibles: {len(tables)}")
            for table in tables[:5]:  # Afficher les 5 premières
                print(f"   - {table[0]}")
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
    return True

def setup_database():
    """Configure la base de données"""
    print("🔧 Configuration de la base de données...")
    
    try:
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
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Test de configuration PostgreSQL...")
    print("=" * 50)
    
    if test_postgresql_connection():
        print("\n🔧 Configuration de la base de données...")
        if setup_database():
            print("\n🎉 Configuration terminée avec succès!")
            print("✅ L'application est prête à utiliser PostgreSQL!")
        else:
            print("\n❌ Erreur lors de la configuration")
    else:
        print("\n❌ Impossible de se connecter à PostgreSQL")