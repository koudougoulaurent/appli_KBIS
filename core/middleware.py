"""
Middleware personnalisé pour optimiser les performances
"""
import time
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les performances
    """
    
    def process_request(self, request):
        """Ajouter des headers de performance"""
        request.start_time = time.time()
        
        # Headers de sécurité et performance
        response = None
        if hasattr(self, 'get_response'):
            response = self.get_response(request)
        
        if response:
            # Headers de cache pour les ressources statiques
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                response['Cache-Control'] = 'public, max-age=31536000'  # 1 an
                response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            
            # Headers de performance
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Header de temps de réponse
            if hasattr(request, 'start_time'):
                process_time = time.time() - request.start_time
                response['X-Process-Time'] = f"{process_time:.3f}s"
        
        return response


class DatabaseQueryOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les requêtes de base de données
    """
    
    def process_response(self, request, response):
        """Optimiser les réponses"""
        # Ajouter des headers de cache pour les pages dynamiques
        if response.status_code == 200:
            if request.path.startswith('/paiements/accords/dashboard/'):
                response['Cache-Control'] = 'private, max-age=300'  # 5 minutes
            elif request.path.startswith('/paiements/accords/liste/'):
                response['Cache-Control'] = 'private, max-age=180'  # 3 minutes
        
        return response


class StaticFilesOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser les fichiers statiques
    """
    
    def process_request(self, request):
        """Optimiser les requêtes de fichiers statiques"""
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Ajouter des headers de cache
            response = HttpResponse()
            response['Cache-Control'] = 'public, max-age=31536000'
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            return response
        
        return None
