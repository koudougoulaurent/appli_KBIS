#!/usr/bin/env python3
"""
Script de réparation PostgreSQL avec --run-syncdb UNIQUEMENT
Pas de migrations, seulement création des tables
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_render')
django.setup()

def fix_postgresql_syncdb_only():
    """Réparation PostgreSQL avec --run-syncdb uniquement"""
    print("🔧 RÉPARATION POSTGRESQL AVEC --run-syncdb UNIQUEMENT")
    print("=" * 60)
    
    try:
        # 1. Tester la connexion PostgreSQL
        print("1️⃣ Test de connexion PostgreSQL...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Connexion PostgreSQL OK: {result}")
        
        # 2. Vérifier la configuration
        from django.conf import settings
        db_config = settings.DATABASES['default']
        print(f"📊 Engine: {db_config['ENGINE']}")
        print(f"📊 Name: {db_config.get('NAME', 'N/A')}")
        
        # 3. FORCER --run-syncdb (pas de migrations)
        print("\n2️⃣ Synchronisation avec --run-syncdb...")
        print("⚠️ IMPORTANT: Pas de migrations, seulement création des tables!")
        
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
        print("✅ Tables créées avec --run-syncdb")
        
        # 4. Vérifier que les tables existent
        print("\n3️⃣ Vérification des tables créées...")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"📊 Tables créées: {len(tables)}")
            
            # Vérifier les tables importantes
            table_names = [table[0] for table in tables]
            important_tables = [
                'utilisateurs_utilisateur',
                'core_configurationentreprise',
                'proprietes_propriete',
                'contrats_contrat',
                'paiements_paiement'
            ]
            
            for table in important_tables:
                if table in table_names:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table} - MANQUANTE")
        
        # 5. Créer les données initiales
        print("\n4️⃣ Création des données initiales...")
        from setup_render import create_groups, create_type_biens, create_devises, create_configuration_entreprise, create_superuser
        
        create_groups()
        create_type_biens()
        create_devises()
        create_configuration_entreprise()
        create_superuser()
        
        print("✅ Données initiales créées")
        
        # 6. Test final
        print("\n5️⃣ Test final...")
        from django.contrib.auth.models import User
        user_count = User.objects.count()
        print(f"📊 Utilisateurs: {user_count}")
        
        if user_count > 0:
            print("🎉 RÉPARATION POSTGRESQL RÉUSSIE!")
            print("✅ Base de données PostgreSQL opérationnelle")
            return True
        else:
            print("❌ Problème: Aucun utilisateur trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la réparation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_postgresql_syncdb_only()
    sys.exit(0 if success else 1)
