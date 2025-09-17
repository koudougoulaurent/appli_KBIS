"""
Système d'optimisation automatique des requêtes
pour l'application de gestion immobilière
"""

import logging
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import time

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Optimiseur de requêtes automatique"""
    
    def __init__(self):
        self.query_patterns = {}
        self.optimization_suggestions = {}
        self.slow_queries = []
    
    def analyze_query(self, query, duration):
        """Analyser une requête et suggérer des optimisations"""
        if duration > 0.1:  # Requêtes > 100ms
            self.slow_queries.append({
                'query': query,
                'duration': duration,
                'timestamp': time.time()
            })
            
            # Analyser le type de requête
            query_type = self._get_query_type(query)
            suggestions = self._get_optimization_suggestions(query, query_type)
            
            if suggestions:
                self.optimization_suggestions[query] = suggestions
                logger.warning(f"Slow query detected: {query[:100]}... ({duration}s)")
                logger.info(f"Optimization suggestions: {suggestions}")
    
    def _get_query_type(self, query):
        """Déterminer le type de requête"""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            return 'SELECT'
        elif query_lower.startswith('insert'):
            return 'INSERT'
        elif query_lower.startswith('update'):
            return 'UPDATE'
        elif query_lower.startswith('delete'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _get_optimization_suggestions(self, query, query_type):
        """Obtenir des suggestions d'optimisation"""
        suggestions = []
        
        if query_type == 'SELECT':
            # Vérifier les jointures manquantes
            if 'join' not in query.lower() and 'from' in query.lower():
                suggestions.append("Considérez l'utilisation de select_related() pour éviter les requêtes N+1")
            
            # Vérifier les requêtes sans LIMIT
            if 'limit' not in query.lower() and 'count' not in query.lower():
                suggestions.append("Ajoutez une limite (LIMIT) pour les requêtes de liste")
            
            # Vérifier les requêtes sans WHERE
            if 'where' not in query.lower() and 'count' not in query.lower():
                suggestions.append("Ajoutez des conditions WHERE pour filtrer les résultats")
            
            # Vérifier les requêtes avec ORDER BY sans index
            if 'order by' in query.lower():
                suggestions.append("Vérifiez que les colonnes ORDER BY sont indexées")
        
        elif query_type == 'UPDATE':
            # Vérifier les mises à jour sans WHERE
            if 'where' not in query.lower():
                suggestions.append("ATTENTION: Mise à jour sans condition WHERE - risque de modification de toutes les lignes")
            
            # Vérifier les mises à jour de colonnes non indexées
            suggestions.append("Vérifiez que les colonnes mises à jour sont indexées si nécessaire")
        
        elif query_type == 'DELETE':
            # Vérifier les suppressions sans WHERE
            if 'where' not in query.lower():
                suggestions.append("ATTENTION: Suppression sans condition WHERE - risque de suppression de toutes les lignes")
        
        return suggestions
    
    def get_optimization_report(self):
        """Obtenir un rapport d'optimisation"""
        return {
            'slow_queries_count': len(self.slow_queries),
            'optimization_suggestions': len(self.optimization_suggestions),
            'slow_queries': self.slow_queries[-10:],  # 10 dernières requêtes lentes
            'suggestions': self.optimization_suggestions,
        }

# Instance globale de l'optimiseur
query_optimizer = QueryOptimizer()

def optimize_queries(func):
    """Décorateur pour optimiser automatiquement les requêtes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        duration = time.time() - start_time
        new_queries = connection.queries[initial_queries:]
        
        # Analyser chaque nouvelle requête
        for query in new_queries:
            query_optimizer.analyze_query(query['sql'], float(query['time']))
        
        return result
    
    return wrapper

def get_optimized_queryset(model_class, **filters):
    """Obtenir un QuerySet optimisé avec les bonnes relations"""
    queryset = model_class.objects.filter(**filters)
    
    # Optimisations automatiques basées sur le modèle
    if hasattr(model_class, '_meta'):
        # Ajouter select_related pour les ForeignKey
        select_related_fields = []
        for field in model_class._meta.fields:
            if field.many_to_one and not field.null:
                select_related_fields.append(field.name)
        
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        
        # Ajouter prefetch_related pour les ManyToManyField
        prefetch_related_fields = []
        for field in model_class._meta.many_to_many:
            prefetch_related_fields.append(field.name)
        
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
    
    return queryset

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
                
                # Créer des index pour les requêtes fréquentes
                self._create_optimization_indexes(cursor)
                
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

def _create_optimization_indexes(cursor):
    """Créer des index d'optimisation"""
    try:
        # Index pour les requêtes fréquentes
        optimization_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_propriete_bailleur ON proprietes_propriete(bailleur_id)",
            "CREATE INDEX IF NOT EXISTS idx_contrat_propriete ON contrats_contrat(propriete_id)",
            "CREATE INDEX IF NOT EXISTS idx_contrat_locataire ON contrats_contrat(locataire_id)",
            "CREATE INDEX IF NOT EXISTS idx_paiement_contrat ON paiements_paiement(contrat_id)",
            "CREATE INDEX IF NOT EXISTS idx_paiement_date ON paiements_paiement(date_paiement)",
            "CREATE INDEX IF NOT EXISTS idx_utilisateur_groups ON auth_user_groups(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_retrait_bailleur ON paiements_retraitbailleur(bailleur_id)",
            "CREATE INDEX IF NOT EXISTS idx_retrait_date ON paiements_retraitbailleur(date_retrait)",
        ]
        
        for index_sql in optimization_indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Impossible de créer l'index: {e}")
        
        logger.info("Index d'optimisation créés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création des index: {e}")

def get_query_performance_stats():
    """Obtenir les statistiques de performance des requêtes"""
    return {
        'total_queries': len(connection.queries),
        'slow_queries': len(query_optimizer.slow_queries),
        'optimization_suggestions': len(query_optimizer.optimization_suggestions),
        'average_query_time': sum(float(q['time']) for q in connection.queries) / len(connection.queries) if connection.queries else 0,
        'optimization_report': query_optimizer.get_optimization_report(),
    }

def clear_query_cache():
    """Nettoyer le cache des requêtes"""
    query_optimizer.slow_queries.clear()
    query_optimizer.optimization_suggestions.clear()
    logger.info("Cache des requêtes nettoyé")

def export_query_analysis():
    """Exporter l'analyse des requêtes"""
    report = query_optimizer.get_optimization_report()
    
    filename = f"query_analysis_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Analyse des requêtes exportée vers {filename}")
    return filename
