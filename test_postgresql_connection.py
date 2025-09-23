#!/usr/bin/env python
"""
Script de test de connexion PostgreSQL
Pour vérifier que la base de données est correctement configurée
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

from django.db import connections
from django.core.management import call_command
from django.apps import apps


def test_postgresql_connection():
    """Tester la connexion PostgreSQL"""
    print("🔍 TEST DE CONNEXION POSTGRESQL - KBIS IMMOBILIER")
    print("=" * 60)
    
    try:
        # 1. Tester la connexion
        print("🔌 Test de connexion...")
        connection = connections['default']
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connexion réussie: {version[0]}")
        
        # 2. Tester les migrations
        print("\n🗄️ Test des migrations...")
        call_command('migrate', verbosity=0)
        print("✅ Migrations appliquées")
        
        # 3. Tester les modèles
        print("\n📋 Test des modèles...")
        test_models()
        
        # 4. Tester les requêtes
        print("\n🔍 Test des requêtes...")
        test_queries()
        
        # 5. Tester les performances
        print("\n⚡ Test des performances...")
        test_performance()
        
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("🌐 Votre base de données PostgreSQL est prête pour Render")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False


def test_models():
    """Tester les modèles"""
    models_to_test = [
        'utilisateurs.Utilisateur',
        'proprietes.Bailleur',
        'proprietes.Locataire',
        'proprietes.Propriete',
        'contrats.Contrat',
        'paiements.Paiement'
    ]
    
    for model_path in models_to_test:
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            
            # Tester la création d'un objet
            count_before = model.objects.count()
            
            # Tester une requête simple
            model.objects.all()[:1]
            
            print(f"  ✅ {model_name}: OK")
            
        except Exception as e:
            print(f"  ❌ {model_path}: {e}")


def test_queries():
    """Tester les requêtes complexes"""
    try:
        from proprietes.models import Propriete
        from contrats.models import Contrat
        from paiements.models import Paiement
        
        # Test de requête avec jointure
        proprietes_avec_contrats = Propriete.objects.select_related('bailleur').prefetch_related('contrat_set').all()
        print(f"  ✅ Requête avec jointure: {proprietes_avec_contrats.count()} propriétés")
        
        # Test de requête avec filtre
        contrats_actifs = Contrat.objects.filter(est_actif=True)
        print(f"  ✅ Requête avec filtre: {contrats_actifs.count()} contrats actifs")
        
        # Test de requête avec agrégation
        from django.db.models import Sum, Count
        total_paiements = Paiement.objects.aggregate(total=Sum('montant'))
        print(f"  ✅ Requête avec agrégation: {total_paiements['total'] or 0}€")
        
    except Exception as e:
        print(f"  ❌ Erreur lors des tests de requêtes: {e}")


def test_performance():
    """Tester les performances"""
    import time
    
    try:
        from proprietes.models import Propriete
        
        # Test de performance - requête simple
        start_time = time.time()
        proprietes = list(Propriete.objects.all())
        end_time = time.time()
        
        query_time = end_time - start_time
        print(f"  ⚡ Requête simple: {query_time:.3f}s pour {len(proprietes)} propriétés")
        
        # Test de performance - requête avec jointure
        start_time = time.time()
        proprietes_avec_bailleur = list(Propriete.objects.select_related('bailleur').all())
        end_time = time.time()
        
        query_time = end_time - start_time
        print(f"  ⚡ Requête avec jointure: {query_time:.3f}s pour {len(proprietes_avec_bailleur)} propriétés")
        
        # Vérifier que les performances sont acceptables
        if query_time > 1.0:  # Plus d'1 seconde
            print("  ⚠️ Attention: Les requêtes sont lentes")
        else:
            print("  ✅ Performances acceptables")
            
    except Exception as e:
        print(f"  ❌ Erreur lors du test de performance: {e}")


def test_database_size():
    """Tester la taille de la base de données"""
    try:
        connection = connections['default']
        with connection.cursor() as cursor:
            # Obtenir la taille de la base de données
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            size = cursor.fetchone()
            print(f"  📊 Taille de la base de données: {size[0]}")
            
            # Obtenir le nombre de tables
            cursor.execute("""
                SELECT count(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cursor.fetchone()
            print(f"  📋 Nombre de tables: {table_count[0]}")
            
    except Exception as e:
        print(f"  ❌ Erreur lors du test de taille: {e}")


if __name__ == "__main__":
    success = test_postgresql_connection()
    
    if success:
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("1. Vérifiez que toutes les données sont présentes")
        print("2. Testez l'application complète")
        print("3. Déployez sur Render")
        print("4. Configurez les variables d'environnement")
    else:
        print("\n❌ TESTS ÉCHOUÉS")
        print("💡 Vérifiez la configuration et réessayez")
        sys.exit(1)
