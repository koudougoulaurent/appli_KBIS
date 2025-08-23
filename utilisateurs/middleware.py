from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware pour optimiser les performances - VERSION AMÉLIORÉE"""
    
    def process_request(self, request):
        # Ajouter un timestamp pour mesurer les performances
        request.start_time = time.time()
        
        # Cache intelligent pour les pages statiques et les dashboards
        cacheable_paths = [
            '/utilisateurs/', 
            '/', 
            '/dashboard/',
            '/proprietes/',
            '/contrats/',
            '/paiements/'
        ]
        
        if request.path in cacheable_paths and request.user.is_authenticated:
            # Créer une clé de cache unique incluant l'utilisateur et le groupe
            user_group = getattr(request.user.groupe_travail, 'nom', 'default') if hasattr(request.user, 'groupe_travail') else 'default'
            cache_key = f"page_cache_{request.path}_{request.user.id}_{user_group}"
            
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit pour {request.path} - Utilisateur: {request.user.username}")
                return cached_response
        
        return None
    
    def process_response(self, request, response):
        # Mesurer le temps de réponse
        if hasattr(request, 'start_time'):
            response_time = time.time() - request.start_time
            
            # Cache intelligent basé sur le temps de réponse et le type de page
            cacheable_paths = [
                '/utilisateurs/', 
                '/', 
                '/dashboard/',
                '/proprietes/',
                '/contrats/',
                '/paiements/'
            ]
            
            if (response_time > 0.3 and  # Réduire le seuil à 0.3s
                request.path in cacheable_paths and 
                request.user.is_authenticated):
                
                user_group = getattr(request.user.groupe_travail, 'nom', 'default') if hasattr(request.user, 'groupe_travail') else 'default'
                cache_key = f"page_cache_{request.path}_{request.user.id}_{user_group}"
                
                # Cache plus long pour les pages lentes
                cache_timeout = 600 if response_time > 1.0 else 300  # 10 min si > 1s, sinon 5 min
                cache.set(cache_key, response, cache_timeout)
                
                logger.info(f"Page mise en cache: {request.path} - Temps: {response_time:.2f}s - Timeout: {cache_timeout}s")
            
            # Logger les performances lentes
            if response_time > 1.0:
                logger.warning(
                    f"Page lente détectée: {request.path} - {response_time:.2f}s - "
                    f"Utilisateur: {request.user.username if request.user.is_authenticated else 'Anonymous'}"
                )
        
        return response

class DatabaseOptimizationMiddleware(MiddlewareMixin):
    """Middleware pour optimiser les requêtes de base de données - VERSION AMÉLIORÉE"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Cache des permissions du groupe avec timeout plus long
            if hasattr(request.user, 'groupe_travail') and request.user.groupe_travail:
                cache_key = f"group_permissions_{request.user.groupe_travail.id}"
                if not cache.get(cache_key):
                    try:
                        permissions = request.user.groupe_travail.get_permissions_list()
                        cache.set(cache_key, permissions, 1800)  # Cache 30 minutes
                    except Exception as e:
                        logger.error(f"Erreur lors de la récupération des permissions: {e}")
            
            # Cache des modules accessibles
            cache_key = f"user_modules_{request.user.id}"
            if not cache.get(cache_key):
                try:
                    modules = request.user.get_accessible_modules()
                    cache.set(cache_key, modules, 1800)  # Cache 30 minutes
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des modules: {e}")
            
            # Cache des informations de profil utilisateur
            cache_key = f"user_profile_{request.user.id}"
            if not cache.get(cache_key):
                try:
                    profile_data = {
                        'username': request.user.username,
                        'email': request.user.email,
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'groupe_travail': request.user.groupe_travail.nom if request.user.groupe_travail else None,
                        'is_superuser': request.user.is_superuser,
                        'is_staff': request.user.is_staff,
                    }
                    cache.set(cache_key, profile_data, 3600)  # Cache 1 heure
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération du profil: {e}")
        
        return None

class CacheOptimizationMiddleware(MiddlewareMixin):
    """Middleware pour optimiser la gestion du cache"""
    
    def process_request(self, request):
        # Nettoyer le cache des utilisateurs inactifs
        if request.user.is_authenticated:
            # Vérifier la dernière activité
            last_activity = request.session.get('last_activity')
            current_time = time.time()
            
            if last_activity and (current_time - last_activity) > 3600:  # 1 heure d'inactivité
                # Nettoyer le cache de l'utilisateur
                from core.optimizations import clear_user_cache
                clear_user_cache(request.user.id)
            
            # Mettre à jour la dernière activité
            request.session['last_activity'] = current_time
        
        return None 