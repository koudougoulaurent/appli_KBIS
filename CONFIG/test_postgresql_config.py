#!/usr/bin/env python3
"""
Script de test pour la configuration PostgreSQL progressive
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

def test_postgresql_connection():
    """Teste la connexion PostgreSQL"""
    print("🧪 TEST DE CONNEXION POSTGRESQL")
    print("=" * 40)
    
    try:
        from django.db import connection
        from django.conf import settings
        
        # Afficher la configuration
        db_config = settings.DATABASES['default']
        print(f"📊 Engine: {db_config['ENGINE']}")
        print(f"📊 Name: {db_config.get('NAME', 'N/A')}")
        print(f"📊 Host: {db_config.get('HOST', 'N/A')}")
        print(f"📊 Port: {db_config.get('PORT', 'N/A')}")
        
        # Tester la connexion
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Connexion PostgreSQL réussie!")
            print(f"📊 Version: {version}")
            
            # Tester une requête simple
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ Test requête: {result}")
            
            # Lister les tables existantes
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"📊 Tables existantes: {len(tables)}")
            for table in tables[:5]:  # Afficher les 5 premières
                print(f"   - {table[0]}")
            if len(tables) > 5:
                print(f"   ... et {len(tables) - 5} autres")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion PostgreSQL: {e}")
        return False

def test_django_models():
    """Teste les modèles Django"""
    print("\n🧪 TEST DES MODÈLES DJANGO")
    print("=" * 40)
    
    try:
        from django.contrib.auth.models import User
        from core.models import ConfigurationEntreprise
        from utilisateurs.models import GroupeTravail
        from proprietes.models import Propriete
        from contrats.models import Contrat
        from paiements.models import Paiement
        
        # Test des modèles de base
        print("✅ Modèles Django chargés avec succès")
        
        # Test des requêtes
        user_count = User.objects.count()
        print(f"📊 Utilisateurs: {user_count}")
        
        try:
            config_count = ConfigurationEntreprise.objects.count()
            print(f"📊 Configurations: {config_count}")
        except:
            print("⚠️ Table ConfigurationEntreprise pas encore créée")
        
        try:
            group_count = GroupeTravail.objects.count()
            print(f"📊 Groupes de travail: {group_count}")
        except:
            print("⚠️ Table GroupeTravail pas encore créée")
        
        try:
            propriete_count = Propriete.objects.count()
            print(f"📊 Propriétés: {propriete_count}")
        except:
            print("⚠️ Table Propriete pas encore créée")
        
        try:
            contrat_count = Contrat.objects.count()
            print(f"📊 Contrats: {contrat_count}")
        except:
            print("⚠️ Table Contrat pas encore créée")
        
        try:
            paiement_count = Paiement.objects.count()
            print(f"📊 Paiements: {paiement_count}")
        except:
            print("⚠️ Table Paiement pas encore créée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test modèles: {e}")
        return False

def test_migrations():
    """Teste les migrations"""
    print("\n🧪 TEST DES MIGRATIONS")
    print("=" * 40)
    
    try:
        from django.core.management import execute_from_command_line
        
        # Tester la synchronisation
        print("🔄 Test de synchronisation...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
        print("✅ Synchronisation réussie")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur migrations: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 TEST DE CONFIGURATION POSTGRESQL PROGRESSIVE")
    print("=" * 60)
    
    # Variables d'environnement
    print("🔧 VARIABLES D'ENVIRONNEMENT:")
    print(f"   RENDER: {os.environ.get('RENDER', 'Non défini')}")
    print(f"   DATABASE_URL: {'Défini' if os.environ.get('DATABASE_URL') else 'Non défini'}")
    print(f"   DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Non défini')}")
    
    # Tests
    tests = [
        ("Connexion PostgreSQL", test_postgresql_connection),
        ("Modèles Django", test_django_models),
        ("Migrations", test_migrations),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ RÉUSSI' if result else '❌ ÉCHOUÉ'}: {test_name}")
    
    # Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ DES TESTS:")
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Résultat: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ Configuration PostgreSQL opérationnelle")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
