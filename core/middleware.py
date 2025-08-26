from core.models import Devise
from django.core.cache import cache

class DeviseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        devise_code = request.session.get('devise_active', 'F CFA')
        
        # Utiliser le cache pour éviter les requêtes répétées
        cache_key = f"devise_{devise_code}"
        devise = cache.get(cache_key)
        
        if devise is None:
            try:
                devise = Devise.objects.get(code=devise_code, actif=True)
                # Mettre en cache pour 1 heure
                cache.set(cache_key, devise, 3600)
            except Devise.DoesNotExist:
                # Récupérer la devise par défaut depuis le cache
                default_cache_key = "devise_F CFA"
                devise = cache.get(default_cache_key)
                
                if devise is None:
                    devise = Devise.objects.get(code='XOF')
                    cache.set(default_cache_key, devise, 3600)
        
        request.devise_active = devise
        response = self.get_response(request)
        return response 