"""
Middleware pour optimiser les performances
"""

from django.db import connection
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
import time

class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les performances
    """
    
    def process_request(self, request):
        """Début de la requête"""
        request.start_time = time.time()
        request.query_count_start = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Fin de la requête"""
        if hasattr(request, 'start_time'):
            # Calculer le temps de traitement
            process_time = time.time() - request.start_time
            
            # Ajouter des headers de performance
            response['X-Process-Time'] = f"{process_time:.3f}s"
            
            # Compter les requêtes
            if hasattr(request, 'query_count_start'):
                query_count = len(connection.queries) - request.query_count_start
                response['X-Query-Count'] = str(query_count)
                
                # Avertir si trop de requêtes
                if query_count > 50:
                    response['X-Performance-Warning'] = 'High query count detected'
            
            # Mettre en cache les statistiques
            cache_key = f"perf_stats_{request.path}"
            cache.set(cache_key, {
                'process_time': process_time,
                'query_count': query_count if hasattr(request, 'query_count_start') else 0,
                'timestamp': time.time()
            }, 300)  # 5 minutes
        
        return response

class DatabaseOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les requêtes de base de données
    """
    
    def process_request(self, request):
        """Optimiser les requêtes"""
        # Activer les logs de requêtes en mode debug
        if hasattr(connection, 'queries'):
            connection.queries_log.clear()
        
        return None
    
    def process_response(self, request, response):
        """Analyser les requêtes après traitement"""
        if hasattr(connection, 'queries') and len(connection.queries) > 0:
            # Analyser les requêtes lentes
            slow_queries = [
                q for q in connection.queries 
                if float(q['time']) > 0.1  # Plus de 100ms
            ]
            
            if slow_queries:
                # Log des requêtes lentes
                print(f"SLOW QUERIES detected on {request.path}:")
                for query in slow_queries:
                    print(f"  - {query['time']}s: {query['sql'][:100]}...")
        
        return response

class CacheMiddleware(MiddlewareMixin):
    """
    Middleware pour la gestion du cache
    """
    
    def process_request(self, request):
        """Gérer le cache des requêtes"""
        # Vérifier si la page est en cache
        if request.method == 'GET' and not request.user.is_authenticated:
            cache_key = f"page_cache_{request.path}_{request.GET.urlencode()}"
            cached_response = cache.get(cache_key)
            
            if cached_response:
                return cached_response
        
        return None
    
    def process_response(self, request, response):
        """Mettre en cache les réponses"""
        if (request.method == 'GET' and 
            response.status_code == 200 and 
            not request.user.is_authenticated and
            'text/html' in response.get('Content-Type', '')):
            
            cache_key = f"page_cache_{request.path}_{request.GET.urlencode()}"
            cache.set(cache_key, response, 300)  # 5 minutes
        
        return response