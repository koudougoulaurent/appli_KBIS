"""
Module d'optimisations pour améliorer les performances de l'application
"""
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def cache_result(timeout=300):
    """Décorateur pour mettre en cache le résultat d'une fonction"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Créer une clé de cache unique
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Essayer de récupérer du cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Exécuter la fonction et mettre en cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """Optimise un queryset avec select_related et prefetch_related"""
    if select_related:
        queryset = queryset.select_related(*select_related)
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    return queryset

def get_cached_stats(user_id=None, timeout=600):
    """Récupère les statistiques mises en cache"""
    cache_key = f"dashboard_stats_{user_id or 'global'}"
    stats = cache.get(cache_key)
    
    if stats is None:
        # Les stats seront calculées dans les vues
        stats = {}
        cache.set(cache_key, stats, timeout)
    
    return stats

def clear_user_cache(user_id):
    """Efface le cache spécifique à un utilisateur"""
    cache_keys = [
        f"dashboard_stats_{user_id}",
        f"user_permissions_{user_id}",
        f"user_modules_{user_id}",
    ]
    
    for key in cache_keys:
        cache.delete(key)

class QueryOptimizer:
    """Classe pour optimiser les requêtes de base de données"""
    
    @staticmethod
    def optimize_dashboard_queries():
        """Optimise les requêtes du dashboard"""
        from paiements.models import Paiement
        from proprietes.models import Propriete, Locataire, Bailleur
        from contrats.models import Contrat
        
        # Optimiser les requêtes de statistiques avec des annotations
        paiements_stats = Paiement.objects.aggregate(
            total=Count('id'),
            valides=Count('id', filter=Q(statut='valide')),
            en_attente=Count('id', filter=Q(statut='en_attente')),
            refuses=Count('id', filter=Q(statut='refuse'))
        )
        
        proprietes_stats = Propriete.objects.aggregate(
            total=Count('id'),
            louees=Count('id', filter=Q(disponible=False)),
            disponibles=Count('id', filter=Q(disponible=True))
        )
        
        contrats_stats = Contrat.objects.aggregate(
            total=Count('id'),
            actifs=Count('id', filter=Q(est_actif=True, est_resilie=False)),
            expires=Count('id', filter=Q(est_resilie=True))
        )
        
        return {
            'paiements': paiements_stats,
            'proprietes': proprietes_stats,
            'contrats': contrats_stats
        }
    
    @staticmethod
    def optimize_recent_data_queries(limit=5):
        """Optimise les requêtes pour les données récentes"""
        from paiements.models import Paiement
        
        # Optimiser les paiements récents avec select_related
        paiements_recents = Paiement.objects.select_related(
            'contrat__locataire',
            'contrat__propriete__bailleur'
        ).order_by('-date_creation')[:limit]
        
        return {
            'paiements_recents': paiements_recents
        }

class TemplateOptimizer:
    """Classe pour optimiser le rendu des templates"""
    
    @staticmethod
    def optimize_template_context(context, user):
        """Optimise le contexte des templates"""
        # Ajouter des informations utilisateur mises en cache
        if user.is_authenticated:
            user_cache_key = f"user_context_{user.id}"
            user_context = cache.get(user_cache_key)
            
            if user_context is None:
                user_context = {
                    'user_groups': list(user.groups.values_list('name', flat=True)),
                    'user_permissions': list(user.user_permissions.values_list('codename', flat=True)),
                    'is_admin': user.is_superuser or user.groups.filter(name='Administrateurs').exists(),
                }
                cache.set(user_cache_key, user_context, 300)  # 5 minutes
            
            context.update(user_context)
        
        return context

def performance_monitor(func):
    """Décorateur pour monitorer les performances des vues"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        # Exécuter la vue
        response = func(request, *args, **kwargs)
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        
        # Logger les performances lentes
        if execution_time > 1.0:  # Plus d'1 seconde
            logger.warning(
                f"Vue lente détectée: {func.__name__} - {execution_time:.2f}s - "
                f"Utilisateur: {request.user.username if request.user.is_authenticated else 'Anonymous'} - "
                f"URL: {request.path}"
            )
        
        # Ajouter le temps d'exécution dans les headers de réponse
        if hasattr(response, 'headers'):
            response.headers['X-Execution-Time'] = f"{execution_time:.3f}s"
        
        return response
    return wrapper
