"""
Middleware d'optimisation des performances
"""
import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware pour optimiser les performances"""
    
    def process_request(self, request):
        """Optimise les requêtes avant traitement"""
        # Démarrer le timer
        request._performance_start = time.time()
        
        # Optimiser les requêtes de base de données
        if hasattr(settings, 'DATABASES'):
            # Activer le cache de requêtes
            connection.queries_log.clear()
        
        return None
    
    def process_response(self, request, response):
        """Optimise la réponse après traitement"""
        # Calculer le temps de traitement
        if hasattr(request, '_performance_start'):
            processing_time = time.time() - request._performance_start
            
            # Logger les requêtes lentes
            if processing_time > 2.0:  # Plus de 2 secondes
                logger.warning(f"Requête lente détectée: {request.path} - {processing_time:.2f}s")
            
            # Ajouter des headers de performance
            if hasattr(response, 'headers'):
                response['X-Processing-Time'] = f"{processing_time:.3f}s"
                response['X-Cache-Status'] = 'MISS' if not hasattr(request, '_cache_hit') else 'HIT'
        
        # Optimiser les réponses JSON
        if isinstance(response, JsonResponse):
            # Ajouter des headers de cache pour les API
            if request.path.startswith('/api/'):
                response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
                response['X-API-Version'] = '1.0'
        
        return response

class CacheOptimizationMiddleware(MiddlewareMixin):
    """Middleware pour optimiser le cache"""
    
    def process_request(self, request):
        """Vérifier le cache avant traitement"""
        # Vérifier le cache pour les requêtes GET
        if request.method == 'GET' and not request.user.is_authenticated:
            cache_key = f"page_cache:{request.path}:{request.GET.urlencode()}"
            cached_response = cache.get(cache_key)
            
            if cached_response:
                request._cache_hit = True
                return cached_response
        
        return None
    
    def process_response(self, request, response):
        """Mettre en cache les réponses appropriées"""
        # Mettre en cache les pages statiques
        if (request.method == 'GET' and 
            response.status_code == 200 and 
            not request.user.is_authenticated and
            not request.path.startswith('/admin/')):
            
            cache_key = f"page_cache:{request.path}:{request.GET.urlencode()}"
            cache.set(cache_key, response, 300)  # 5 minutes
        
        return response

class DatabaseOptimizationMiddleware(MiddlewareMixin):
    """Middleware pour optimiser les requêtes de base de données"""
    
    def process_request(self, request):
        """Optimiser les requêtes de base de données"""
        # Activer le debug des requêtes en mode développement
        if settings.DEBUG:
            from django.db import connection
            connection.queries_log.clear()
        
        return None
    
    def process_response(self, request, response):
        """Analyser et optimiser les requêtes"""
        if settings.DEBUG and hasattr(connection, 'queries'):
            queries = connection.queries
            query_count = len(queries)
            
            # Logger les requêtes multiples
            if query_count > 10:
                logger.warning(f"Trop de requêtes: {query_count} pour {request.path}")
                
                # Identifier les requêtes lentes
                slow_queries = [q for q in queries if float(q['time']) > 0.1]
                if slow_queries:
                    logger.warning(f"Requêtes lentes détectées: {len(slow_queries)}")
                    for query in slow_queries[:3]:  # Afficher les 3 plus lentes
                        logger.warning(f"  - {query['time']}s: {query['sql'][:100]}...")
            
            # Ajouter des headers de debug
            if hasattr(response, 'headers'):
                response['X-Query-Count'] = str(query_count)
                response['X-Debug-Queries'] = 'enabled'
        
        return response

class StaticFilesOptimizationMiddleware(MiddlewareMixin):
    """Middleware pour optimiser les fichiers statiques"""
    
    def process_response(self, request, response):
        """Optimiser les réponses de fichiers statiques"""
        # Ajouter des headers de cache pour les fichiers statiques
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'))):
            
            if hasattr(response, 'headers'):
                response['Cache-Control'] = 'public, max-age=31536000'  # 1 an
                response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        
        return response

class AntiRefreshLoopMiddleware(MiddlewareMixin):
    """Middleware pour éviter les boucles de rafraîchissement"""
    
    def process_request(self, request):
        """Détecter et prévenir les boucles de rafraîchissement"""
        # Vérifier les headers de requête répétitives
        if hasattr(request, 'META'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            referer = request.META.get('HTTP_REFERER', '')
            
            # Détecter les requêtes automatiques répétitives
            if 'bot' in user_agent.lower() or 'crawler' in user_agent.lower():
                # Limiter les requêtes de bots
                cache_key = f"bot_limit:{request.META.get('REMOTE_ADDR', 'unknown')}"
                if cache.get(cache_key):
                    return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
                cache.set(cache_key, True, 60)  # 1 minute
        
        return None
    
    def process_response(self, request, response):
        """Ajouter des headers pour éviter les boucles"""
        if hasattr(response, 'headers'):
            # Ajouter des headers pour éviter les boucles de rafraîchissement
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Pour les pages du dashboard, ajouter un header de stabilité
            if request.path.startswith('/core/dashboard/'):
                response['X-Dashboard-Stable'] = 'true'
                response['Cache-Control'] = 'private, max-age=60'  # 1 minute pour le dashboard
        
        return response
