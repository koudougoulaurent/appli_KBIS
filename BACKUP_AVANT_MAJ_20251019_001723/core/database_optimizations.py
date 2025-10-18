"""
Optimisations spécifiques de base de données pour améliorer les performances
de l'application de gestion immobilière
"""

import logging
from django.db import connection, transaction
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import time

logger = logging.getLogger(__name__)

def optimize_database_connection():
    """Optimiser la connexion à la base de données"""
    try:
        with connection.cursor() as cursor:
            # Optimisations SQLite
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
                cursor.execute("PRAGMA page_size=4096")
                cursor.execute("PRAGMA max_page_count=1073741824")  # 1GB
                
                logger.info("Optimisations SQLite appliquées avec succès")
            
            # Optimisations PostgreSQL
            elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SET work_mem = '4MB'")
                cursor.execute("SET maintenance_work_mem = '64MB'")
                cursor.execute("SET shared_buffers = '256MB'")
                cursor.execute("SET effective_cache_size = '1GB'")
                
                logger.info("Optimisations PostgreSQL appliquées avec succès")
            
            # Optimisations MySQL
            elif 'mysql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SET SESSION innodb_buffer_pool_size = 268435456")  # 256MB
                cursor.execute("SET SESSION query_cache_size = 33554432")  # 32MB
                cursor.execute("SET SESSION query_cache_type = 1")
                
                logger.info("Optimisations MySQL appliquées avec succès")
                
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation de la base de données: {e}")

def query_optimizer(timeout=300):
    """Décorateur pour optimiser les requêtes de base de données"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Vérifier le cache
            cache_key = f"db_query_{func.__name__}_{hash(str(args) + str(kwargs))}"
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Résultat récupéré du cache pour {func.__name__}")
                return cached_result
            
            # Exécuter la fonction
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Logger les requêtes lentes
            if execution_time > 0.5:
                logger.warning(
                    f"Requête lente détectée: {func.__name__} - "
                    f"Temps: {execution_time:.3f}s"
                )
            
            # Mettre en cache le résultat
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def bulk_operation_optimizer(batch_size=100):
    """Décorateur pour optimiser les opérations en lot"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Traiter par lots si c'est une liste
            if 'objects' in kwargs and isinstance(kwargs['objects'], list):
                objects = kwargs['objects']
                results = []
                
                for i in range(0, len(objects), batch_size):
                    batch = objects[i:i + batch_size]
                    kwargs['objects'] = batch
                    batch_result = func(*args, **kwargs)
                    results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
                
                return results
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class DatabaseQueryOptimizer:
    """Classe pour optimiser les requêtes de base de données"""
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None, only=None, defer=None):
        """Optimiser un queryset avec les bonnes pratiques"""
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        if only:
            queryset = queryset.only(*only)
        
        if defer:
            queryset = queryset.defer(*defer)
        
        return queryset
    
    @staticmethod
    def optimize_aggregation(queryset, annotations=None, aggregations=None):
        """Optimiser les agrégations"""
        if annotations:
            queryset = queryset.annotate(**annotations)
        
        if aggregations:
            return queryset.aggregate(**aggregations)
        
        return queryset
    
    @staticmethod
    def optimize_count(queryset, use_cache=True):
        """Optimiser le comptage d'objets"""
        if use_cache:
            # Utiliser le cache pour les comptages fréquents
            cache_key = f"count_{queryset.model._meta.db_table}_{hash(str(queryset.query))}"
            cached_count = cache.get(cache_key)
            
            if cached_count is not None:
                return cached_count
            
            count = queryset.count()
            cache.set(cache_key, count, 300)  # Cache 5 minutes
            return count
        
        return queryset.count()
    
    @staticmethod
    def optimize_exists(queryset):
        """Optimiser la vérification d'existence"""
        return queryset.exists()
    
    @staticmethod
    def optimize_values_list(queryset, fields, flat=False):
        """Optimiser la récupération de valeurs"""
        return queryset.values_list(*fields, flat=flat)

class DatabaseIndexOptimizer:
    """Classe pour optimiser les index de base de données"""
    
    @staticmethod
    def create_index_if_not_exists(table_name, column_name, index_name=None):
        """Créer un index s'il n'existe pas"""
        if not index_name:
            index_name = f"idx_{table_name}_{column_name}"
        
        try:
            with connection.cursor() as cursor:
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})")
                elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table_name} ({column_name})")
                elif 'mysql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute(f"CREATE INDEX {index_name} ON {table_name} ({column_name})")
                
                logger.info(f"Index créé: {index_name} sur {table_name}.{column_name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index {index_name}: {e}")
    
    @staticmethod
    def analyze_table(table_name):
        """Analyser une table pour optimiser les requêtes"""
        try:
            with connection.cursor() as cursor:
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute(f"ANALYZE {table_name}")
                elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute(f"ANALYZE {table_name}")
                elif 'mysql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute(f"ANALYZE TABLE {table_name}")
                
                logger.info(f"Table analysée: {table_name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la table {table_name}: {e}")

class DatabaseConnectionOptimizer:
    """Classe pour optimiser les connexions à la base de données"""
    
    @staticmethod
    def optimize_connection_pool():
        """Optimiser le pool de connexions"""
        try:
            with connection.cursor() as cursor:
                # Optimisations générales
                cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
                
                # Optimisations de performance
                cursor.execute("SET SESSION innodb_flush_log_at_trx_commit = 2")
                cursor.execute("SET SESSION sync_binlog = 0")
                
                logger.info("Pool de connexions optimisé")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation du pool de connexions: {e}")
    
    @staticmethod
    def close_idle_connections():
        """Fermer les connexions inactives"""
        try:
            connection.close()
            logger.info("Connexions inactives fermées")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture des connexions: {e}")

def optimize_database_performance():
    """Fonction principale pour optimiser les performances de la base de données"""
    try:
        # Optimiser la connexion
        optimize_database_connection()
        
        # Optimiser le pool de connexions
        DatabaseConnectionOptimizer.optimize_connection_pool()
        
        # Créer des index optimaux
        DatabaseIndexOptimizer.create_index_if_not_exists('core_propriete', 'disponible')
        DatabaseIndexOptimizer.create_index_if_not_exists('core_propriete', 'bailleur_id')
        DatabaseIndexOptimizer.create_index_if_not_exists('contrats_contrat', 'est_actif')
        DatabaseIndexOptimizer.create_index_if_not_exists('contrats_contrat', 'date_debut')
        DatabaseIndexOptimizer.create_index_if_not_exists('paiements_paiement', 'statut')
        DatabaseIndexOptimizer.create_index_if_not_exists('paiements_paiement', 'date_paiement')
        
        # Analyser les tables principales
        DatabaseIndexOptimizer.analyze_table('core_propriete')
        DatabaseIndexOptimizer.analyze_table('contrats_contrat')
        DatabaseIndexOptimizer.analyze_table('paiements_paiement')
        
        logger.info("Optimisations de base de données appliquées avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation de la base de données: {e}")
        return False

def monitor_database_performance():
    """Monitorer les performances de la base de données"""
    try:
        with connection.cursor() as cursor:
            # Récupérer les statistiques de performance
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("PRAGMA stats")
                stats = cursor.fetchall()
                
                # Logger les statistiques
                for stat in stats:
                    logger.info(f"Statistique SQLite: {stat}")
            
            # Récupérer le nombre de connexions actives
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            logger.info(f"Nombre de tables dans la base: {table_count}")
            
    except Exception as e:
        logger.error(f"Erreur lors du monitoring de la base de données: {e}")

# Initialisation automatique des optimisations
if settings.DEBUG:
    optimize_database_performance()
