"""
Module d'optimisations avancées pour améliorer les performances
de l'application de gestion immobilière
"""

import time
import logging
from functools import wraps
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

logger = logging.getLogger(__name__)

def performance_monitor(func):
    """Décorateur pour surveiller les performances des fonctions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_queries = len(connection.queries)
            
            execution_time = end_time - start_time
            queries_count = end_queries - start_queries
            
            if execution_time > 0.5:  # Log si plus de 0.5s
                logger.warning(
                    f"Fonction lente: {func.__name__} - "
                    f"Temps: {execution_time:.3f}s - "
                    f"Requêtes: {queries_count}"
                )
            
            # Mettre en cache les résultats lents
            if execution_time > 1.0:
                cache_key = f"slow_func_{func.__name__}_{hash(str(args) + str(kwargs))}"
                cache.set(cache_key, result, 300)  # Cache 5 minutes
    
    return wrapper

def query_optimizer(func):
    """Décorateur pour optimiser les requêtes de base de données"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Vérifier le cache avant d'exécuter
        cache_key = f"query_cache_{func.__name__}_{hash(str(args) + str(kwargs))}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # Exécuter la fonction
        result = func(*args, **kwargs)
        
        # Mettre en cache le résultat
        cache.set(cache_key, result, 1800)  # Cache 30 minutes
        
        return result
    
    return wrapper

def clear_user_cache(user_id):
    """Nettoyer le cache d'un utilisateur spécifique"""
    try:
        # Supprimer tous les caches liés à l'utilisateur
        cache_keys_to_delete = [
            f"user_profile_{user_id}",
            f"user_modules_{user_id}",
            f"group_permissions_{user_id}",
            f"page_cache_*_{user_id}_*"
        ]
        
        for pattern in cache_keys_to_delete:
            if '*' in pattern:
                # Pour les patterns avec wildcard, on ne peut pas les supprimer directement
                # mais on peut nettoyer les clés connues
                continue
            cache.delete(pattern)
        
        logger.info(f"Cache nettoyé pour l'utilisateur {user_id}")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du cache: {e}")

def optimize_database_queries():
    """Optimisations générales de la base de données"""
    with connection.cursor() as cursor:
        # Activer les optimisations SQLite
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB

def get_cached_data(key, default=None, timeout=300):
    """Récupérer des données en cache avec fallback"""
    try:
        cached_data = cache.get(key)
        if cached_data is not None:
            return cached_data
        return default
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du cache {key}: {e}")
        return default

def set_cached_data(key, data, timeout=300):
    """Mettre des données en cache de manière sécurisée"""
    try:
        cache.set(key, data, timeout)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise en cache de {key}: {e}")
        return False

def bulk_cache_operations(operations):
    """Effectuer des opérations de cache en lot"""
    results = []
    for operation in operations:
        try:
            if operation['type'] == 'set':
                cache.set(operation['key'], operation['value'], operation.get('timeout', 300))
                results.append(True)
            elif operation['type'] == 'delete':
                cache.delete(operation['key'])
                results.append(True)
            elif operation['type'] == 'get':
                value = cache.get(operation['key'])
                results.append(value)
        except Exception as e:
            logger.error(f"Erreur lors de l'opération de cache {operation}: {e}")
            results.append(False)
    
    return results

# Optimisations spécifiques pour les vues
def cache_page_optimized(timeout=300, key_prefix=''):
    """Version optimisée du décorateur cache_page"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Créer une clé de cache unique
            cache_key = f"{key_prefix}_{request.path}_{request.user.id if request.user.is_authenticated else 'anonymous'}"
            
            # Vérifier le cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Exécuter la vue
            response = view_func(request, *args, **kwargs)
            
            # Mettre en cache seulement si la réponse est valide
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)
            
            return response
        return wrapper
    return decorator

# Optimisations pour les modèles
class ModelOptimizer:
    """Classe utilitaire pour optimiser les requêtes de modèles"""
    
    @staticmethod
    def prefetch_related_fields(model_class, fields):
        """Précharger les champs liés pour éviter les requêtes N+1"""
        return model_class.objects.select_related(*fields)
    
    @staticmethod
    def bulk_create_optimized(objs, batch_size=100):
        """Créer des objets en lot de manière optimisée"""
        from django.db import transaction
        
        with transaction.atomic():
            for i in range(0, len(objs), batch_size):
                batch = objs[i:i + batch_size]
                model_class = type(batch[0])
                model_class.objects.bulk_create(batch, ignore_conflicts=True)
    
    @staticmethod
    def update_queryset_optimized(queryset, updates, batch_size=100):
        """Mettre à jour un queryset de manière optimisée"""
        from django.db import transaction
        
        with transaction.atomic():
            for i in range(0, queryset.count(), batch_size):
                batch = queryset[i:i + batch_size]
                batch.update(**updates)

# Configuration des optimisations
def configure_performance_optimizations():
    """Configurer toutes les optimisations de performance"""
    try:
        # Optimiser la base de données
        optimize_database_queries()
        
        # Configurer le cache
        cache.set('performance_configured', True, 3600)
        
        logger.info("Optimisations de performance configurées avec succès")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la configuration des optimisations: {e}")
        return False

# Initialisation automatique
if settings.DEBUG:
    configure_performance_optimizations()
