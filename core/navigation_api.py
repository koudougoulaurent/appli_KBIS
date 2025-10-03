"""
API Views pour la navigation dynamique et la recherche intelligente
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import json

from .dynamic_navigation import DynamicNavigationSystem
from .smart_search import SmartSearchSystem

@login_required
@require_http_methods(["GET"])
def get_navigation_context(request):
    """
    API pour récupérer le contexte de navigation dynamique
    """
    current_module = request.GET.get('module', '')
    object_id = request.GET.get('object_id', '')
    
    try:
        navigation = DynamicNavigationSystem.get_contextual_links(
            request, current_module, object_id
        )
        
        return JsonResponse({
            'success': True,
            'navigation': navigation
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
@cache_page(60 * 5)  # Cache de 5 minutes
def smart_search_api(request):
    """
    API pour la recherche intelligente
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({
            'success': False,
            'error': 'Requête de recherche vide'
        }, status=400)
    
    try:
        results = SmartSearchSystem.search_all_modules(query, request)
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def recent_searches_api(request):
    """
    API pour récupérer les recherches récentes
    """
    try:
        recent_searches = SmartSearchSystem.get_recent_searches(request)
        
        return JsonResponse({
            'success': True,
            'searches': recent_searches
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def save_search_api(request):
    """
    API pour sauvegarder une recherche
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if query:
            SmartSearchSystem.save_search(request, query)
            
        return JsonResponse({
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def trending_searches_api(request):
    """
    API pour récupérer les recherches tendances
    """
    try:
        trending = SmartSearchSystem.get_trending_searches()
        
        return JsonResponse({
            'success': True,
            'trending': trending
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def module_stats_api(request):
    """
    API pour récupérer les statistiques des modules
    """
    module = request.GET.get('module', '')
    
    try:
        stats = {}
        
        if module == 'proprietes':
            from proprietes.models import Propriete, Bailleur, Locataire
            stats = {
                'total_proprietes': Propriete.objects.filter(is_deleted=False).count(),
                'total_bailleurs': Bailleur.objects.filter(is_deleted=False).count(),
                'total_locataires': Locataire.objects.filter(is_deleted=False).count(),
                'proprietes_actives': Propriete.objects.filter(
                    is_deleted=False, 
                    statut='active'
                ).count()
            }
            
        elif module == 'paiements':
            from paiements.models import Paiement
            from django.db.models import Sum
            stats = {
                'total_paiements': Paiement.objects.filter(is_deleted=False).count(),
                'paiements_valides': Paiement.objects.filter(
                    is_deleted=False, 
                    statut='valide'
                ).count(),
                'paiements_en_attente': Paiement.objects.filter(
                    is_deleted=False, 
                    statut='en_attente'
                ).count(),
                'montant_total': Paiement.objects.filter(
                    is_deleted=False, 
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
            }
            
        elif module == 'contrats':
            from contrats.models import Contrat
            from datetime import date, timedelta
            stats = {
                'total_contrats': Contrat.objects.filter(is_deleted=False).count(),
                'contrats_actifs': Contrat.objects.filter(
                    is_deleted=False, 
                    statut='actif'
                ).count(),
                'contrats_expirant': Contrat.objects.filter(
                    is_deleted=False,
                    statut='actif',
                    date_fin__lte=date.today() + timedelta(days=30)
                ).count()
            }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

