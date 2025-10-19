"""
Middleware pour détecter et bloquer les boucles de rafraîchissement
"""
import time
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class AntiLoopMiddleware(MiddlewareMixin):
    """Middleware pour détecter et bloquer les boucles de rafraîchissement"""
    
    def process_request(self, request):
        """Détecter les requêtes en boucle"""
        # Vérifier seulement les requêtes AJAX vers l'API dashboard
        if (request.path.startswith('/core/api/dashboard-stats/') and 
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'):
            
            # Obtenir l'IP et l'User-Agent
            ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Créer une clé unique pour cette combinaison
            cache_key = f"dashboard_refresh:{ip}:{hash(user_agent)}"
            
            # Vérifier le cache
            last_request = cache.get(cache_key)
            now = time.time()
            
            if last_request:
                time_diff = now - last_request
                
                # Si la requête est trop récente (moins de 5 secondes), la bloquer
                if time_diff < 5:
                    logger.warning(f"Requête en boucle détectée: {ip} - {time_diff:.2f}s")
                    return JsonResponse({
                        'success': False,
                        'error': 'Trop de requêtes rapides',
                        'retry_after': 5
                    }, status=429)
                
                # Si plusieurs requêtes en peu de temps, bloquer temporairement
                if time_diff < 30:
                    # Compter les requêtes récentes
                    recent_requests = cache.get(f"{cache_key}:count", 0)
                    if recent_requests > 3:  # Plus de 3 requêtes en 30 secondes
                        logger.warning(f"Trop de requêtes détectées: {ip} - {recent_requests}")
                        cache.set(f"{cache_key}:blocked", True, 60)  # Bloquer 1 minute
                        return JsonResponse({
                            'success': False,
                            'error': 'Trop de requêtes, veuillez patienter',
                            'retry_after': 60
                        }, status=429)
                    else:
                        cache.set(f"{cache_key}:count", recent_requests + 1, 30)
                else:
                    # Reset le compteur si plus de 30 secondes
                    cache.set(f"{cache_key}:count", 1, 30)
            else:
                # Première requête
                cache.set(f"{cache_key}:count", 1, 30)
            
            # Vérifier si l'IP est bloquée
            if cache.get(f"{cache_key}:blocked"):
                return JsonResponse({
                    'success': False,
                    'error': 'Accès temporairement bloqué',
                    'retry_after': 60
                }, status=429)
            
            # Enregistrer cette requête
            cache.set(cache_key, now, 60)  # Garder 1 minute
            
            # Ajouter des headers pour éviter les boucles
            request._prevent_loop = True
        
        return None
    
    def process_response(self, request, response):
        """Ajouter des headers pour éviter les boucles"""
        if hasattr(request, '_prevent_loop'):
            # Ajouter des headers pour éviter les boucles
            response['X-Rate-Limit-Remaining'] = '10'
            response['X-Rate-Limit-Reset'] = str(int(time.time()) + 60)
            response['Cache-Control'] = 'private, max-age=60'
            response['X-Prevent-Loop'] = 'true'
        
        return response
    
    def get_client_ip(self, request):
        """Obtenir l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
