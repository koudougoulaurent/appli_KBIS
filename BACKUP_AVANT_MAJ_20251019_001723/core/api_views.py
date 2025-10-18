"""
API Views pour les actions rapides et optimisations de performance
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings
import json

from .quick_actions_generator import QuickActionsGenerator
from .utils import check_group_permissions

@login_required
@require_http_methods(["GET"])
@cache_page(60 * 5)  # Cache de 5 minutes
def quick_actions_api(request):
    """
    API pour récupérer les actions rapides de manière asynchrone
    """
    page = request.GET.get('page', '')
    object_id = request.GET.get('object_id', '')
    
    try:
        # Déterminer le type de page et récupérer les actions
        if 'bailleur' in page:
            from proprietes.models import Bailleur
            try:
                bailleur = Bailleur.objects.get(pk=object_id)
                actions = QuickActionsGenerator.get_actions_for_bailleur(bailleur, request)
            except Bailleur.DoesNotExist:
                actions = []
                
        elif 'locataire' in page:
            # Locataire model not yet implemented
            actions = []
                
        elif 'propriete' in page:
            from proprietes.models import Propriete
            try:
                propriete = Propriete.objects.get(pk=object_id)
                actions = QuickActionsGenerator.get_actions_for_propriete(propriete, request)
            except Propriete.DoesNotExist:
                actions = []
                
        elif 'contrat' in page:
            from contrats.models import Contrat
            try:
                contrat = Contrat.objects.get(pk=object_id)
                actions = QuickActionsGenerator.get_actions_for_contrat(contrat, request)
            except Contrat.DoesNotExist:
                actions = []
                
        elif 'paiement' in page:
            from paiements.models import Paiement
            try:
                paiement = Paiement.objects.get(pk=object_id)
                actions = QuickActionsGenerator.get_actions_for_paiement(paiement, request)
            except Paiement.DoesNotExist:
                actions = []
                
        else:
            # Actions par défaut pour les pages de liste
            actions = QuickActionsGenerator.get_default_actions(request)
            
        return JsonResponse({
            'success': True,
            'actions': actions,
            'count': len(actions)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'actions': []
        }, status=500)

@login_required
@require_http_methods(["GET"])
def performance_stats(request):
    """
    API pour les statistiques de performance
    """
    try:
        # Statistiques de cache
        cache_stats = {
            'cache_size': len(cache._cache) if hasattr(cache, '_cache') else 0,
            'cache_hits': getattr(cache, '_cache_hits', 0),
            'cache_misses': getattr(cache, '_cache_misses', 0),
        }
        
        # Statistiques de base de données
        from django.db import connection
        db_stats = {
            'queries_count': len(connection.queries),
            'queries_time': sum(float(q['time']) for q in connection.queries),
        }
        
        return JsonResponse({
            'success': True,
            'cache': cache_stats,
            'database': db_stats,
            'timestamp': cache.get('performance_timestamp', 0)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def clear_cache(request):
    """
    API pour vider le cache
    """
    try:
        cache.clear()
        return JsonResponse({
            'success': True,
            'message': 'Cache vidé avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def health_check(request):
    """
    Vérification de santé de l'API
    """
    try:
        # Vérifier la base de données
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Vérifier le cache
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check') == 'ok'
        
        return JsonResponse({
            'success': True,
            'database': 'ok',
            'cache': 'ok' if cache_status else 'error',
            'timestamp': cache.get('health_timestamp', 0)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'database': 'error',
            'cache': 'error'
        }, status=500)