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
                # Essayer de récupérer la devise par défaut
                try:
                    devise = Devise.objects.filter(par_defaut=True, actif=True).first()
                    if devise:
                        cache.set(cache_key, devise, 3600)
                    else:
                        # Essayer de récupérer n'importe quelle devise active
                        devise = Devise.objects.filter(actif=True).first()
                        if devise:
                            cache.set(cache_key, devise, 3600)
                        else:
                            # Créer une devise par défaut si aucune n'existe
                            devise = self._create_default_devise()
                            cache.set(cache_key, devise, 3600)
                except Exception:
                    # En dernier recours, créer une devise par défaut
                    devise = self._create_default_devise()
                    cache.set(cache_key, devise, 3600)
        
        request.devise_active = devise
        response = self.get_response(request)
        return response
    
    def _create_default_devise(self):
        """Crée une devise par défaut si aucune n'existe."""
        try:
            devise = Devise.objects.create(
                code='F CFA',
                nom='Franc CFA',
                symbole='F CFA',
                taux_change=1.0,
                actif=True,
                par_defaut=True
            )
            return devise
        except Exception:
            # Si la création échoue, retourner un objet Devise minimal
            # pour éviter les erreurs dans les templates
            class MockDevise:
                def __init__(self):
                    self.code = 'F CFA'
                    self.nom = 'Franc CFA'
                    self.symbole = 'F CFA'
                    self.taux_change = 1.0
                    self.actif = True
                    self.par_defaut = True
                
                def __str__(self):
                    return f"{self.nom} ({self.code})"
            
            return MockDevise() 