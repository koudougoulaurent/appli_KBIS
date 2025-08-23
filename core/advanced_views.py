"""
Vues avancées avec système de recherche et tri intelligent
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .search_engine import search_engine, sorting_engine, filter_builder


class AdvancedSearchView:
    """
    Vue de base pour la recherche avancée
    """
    
    def __init__(self, model_class, template_name, context_name):
        self.model_class = model_class
        self.template_name = template_name
        self.context_name = context_name
    
    def __call__(self, request):
        return self.search_view(request)
    
    def search_view(self, request):
        """
        Vue de recherche avancée avec moteur intelligent
        """
        # Récupération des paramètres
        search_query = request.GET.get('q', '')
        sort_type = request.GET.get('sort', 'relevance')
        page = request.GET.get('page', 1)
        filters = self._extract_filters(request)
        
        # Analyse intelligente de la requête
        parsed_query = search_engine.parse_search_query(search_query)
        
        # Construction de la requête de base
        queryset = self.model_class.objects.all()
        
        # Application des filtres avancés
        if parsed_query:
            advanced_query = search_engine.build_advanced_query(
                self.model_class, parsed_query, filters
            )
            queryset = queryset.filter(advanced_query)
        
        # Tri intelligent
        if sort_type == 'relevance' and parsed_query:
            ordering = search_engine.get_smart_ordering(
                self.model_class, parsed_query
            )
            queryset = queryset.order_by(*ordering)
        else:
            queryset = sorting_engine.sort_queryset(
                queryset, sort_type, {'search_query': search_query}
            )
        
        # Pagination
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(page)
        
        # Suggestions de recherche
        suggestions = search_engine.get_search_suggestions(
            search_query, self.model_class
        )
        
        # Analytics de recherche
        analytics = search_engine.get_search_analytics(search_query)
        
        # Statistiques avancées
        stats = self._get_advanced_stats(queryset, filters)
        
        context = {
            self.context_name: page_obj,
            'search_query': search_query,
            'parsed_query': parsed_query,
            'suggestions': suggestions,
            'analytics': analytics,
            'stats': stats,
            'filters': filters,
            'sort_type': sort_type,
            'total_results': queryset.count(),
            'search_time': self._measure_search_time(),
        }
        
        return render(request, self.template_name, context)
    
    def _extract_filters(self, request):
        """Extrait les filtres de la requête"""
        filters = {}
        
        # Filtres de base
        for key in ['prix_min', 'prix_max', 'surface_min', 'surface_max', 
                   'ville', 'type', 'statut', 'disponible']:
            value = request.GET.get(key)
            if value:
                filters[key] = value
        
        # Filtres de date
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        if date_debut or date_fin:
            filters['date_range'] = {
                'debut': date_debut,
                'fin': date_fin
            }
        
        return filters
    
    def _get_advanced_stats(self, queryset, filters):
        """Calcule des statistiques avancées"""
        stats = {
            'total': queryset.count(),
            'categories': {},
            'trends': {},
            'insights': []
        }
        
        # Statistiques par catégorie selon le modèle
        model_name = self.model_class.__name__.lower()
        
        if model_name == 'propriete':
            stats.update(self._get_propriete_stats(queryset))
        elif model_name == 'contrat':
            stats.update(self._get_contrat_stats(queryset))
        elif model_name == 'paiement':
            stats.update(self._get_paiement_stats(queryset))
        
        return stats
    
    def _get_propriete_stats(self, queryset):
        """Statistiques spécifiques aux propriétés"""
        stats = {}
        
        # Répartition par ville
        stats['par_ville'] = queryset.values('ville').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Répartition par type
        stats['par_type'] = queryset.values('type_bien__nom').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Statistiques de prix
        prix_stats = queryset.aggregate(
            prix_moyen=Avg('loyer_actuel'),
            prix_min=Min('loyer_actuel'),
            prix_max=Max('loyer_actuel')
        )
        stats['prix'] = prix_stats
        
        # Répartition par disponibilité
        stats['disponibilite'] = {
            'disponibles': queryset.filter(disponible=True).count(),
            'louees': queryset.filter(disponible=False).count()
        }
        
        return stats
    
    def _get_contrat_stats(self, queryset):
        """Statistiques spécifiques aux contrats"""
        stats = {}
        
        # Répartition par statut
        stats['par_statut'] = queryset.values('statut').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Loyer moyen par type de bien
        stats['loyer_par_type'] = queryset.values(
            'propriete__type_bien__nom'
        ).annotate(
            loyer_moyen=Avg('loyer_mensuel')
        ).order_by('-loyer_moyen')
        
        return stats
    
    def _get_paiement_stats(self, queryset):
        """Statistiques spécifiques aux paiements"""
        stats = {}
        
        # Répartition par statut
        stats['par_statut'] = queryset.values('statut').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-total')
        
        # Évolution mensuelle
        stats['evolution_mensuelle'] = queryset.extra(
            select={'mois': "EXTRACT(month FROM date_paiement)"}
        ).values('mois').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('mois')
        
        return stats
    
    def _measure_search_time(self):
        """Mesure le temps de recherche (simulation)"""
        return 0.15  # Temps simulé en secondes


class IntelligentListView:
    """
    Vue de liste intelligente avec fonctionnalités avancées
    """
    
    def __init__(self, model_class, template_name, context_name):
        self.model_class = model_class
        self.template_name = template_name
        self.context_name = context_name
    
    def __call__(self, request):
        return self.list_view(request)
    
    def list_view(self, request):
        """
        Vue de liste avec tri et filtres intelligents
        """
        # Récupération des paramètres
        sort_type = request.GET.get('sort', 'smart')
        filter_type = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        
        # Requête de base
        queryset = self.model_class.objects.all()
        
        # Application des filtres intelligents
        if filter_type:
            queryset = self._apply_intelligent_filters(queryset, filter_type, request)
        
        # Tri intelligent
        queryset = sorting_engine.sort_queryset(
            queryset, sort_type, {'request': request}
        )
        
        # Pagination
        paginator = Paginator(queryset, 25)
        page_obj = paginator.get_page(page)
        
        # Statistiques intelligentes
        stats = self._get_intelligent_stats(queryset)
        
        # Suggestions de tri et filtres
        suggestions = self._get_suggestions(queryset, request)
        
        context = {
            self.context_name: page_obj,
            'stats': stats,
            'suggestions': suggestions,
            'sort_type': sort_type,
            'filter_type': filter_type,
            'total_results': queryset.count(),
        }
        
        return render(request, self.template_name, context)
    
    def _apply_intelligent_filters(self, queryset, filter_type, request):
        """Applique des filtres intelligents"""
        if filter_type == 'recent':
            # Éléments récents (7 derniers jours)
            date_limit = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(date_creation__gte=date_limit)
        
        elif filter_type == 'urgent':
            # Éléments urgents
            queryset = queryset.filter(priorite__gte=8)
        
        elif filter_type == 'problematic':
            # Éléments problématiques
            queryset = queryset.filter(
                Q(statut='en_attente') | Q(statut='probleme')
            )
        
        elif filter_type == 'high_value':
            # Éléments à haute valeur
            queryset = queryset.filter(loyer_actuel__gte=1000)
        
        return queryset
    
    def _get_intelligent_stats(self, queryset):
        """Calcule des statistiques intelligentes"""
        stats = {
            'total': queryset.count(),
            'insights': [],
            'recommendations': []
        }
        
        # Insights basés sur les données
        if queryset.count() > 0:
            # Insight sur la répartition
            if hasattr(queryset.first(), 'statut'):
                statut_distribution = queryset.values('statut').annotate(
                    count=Count('id')
                )
                dominant_statut = max(statut_distribution, key=lambda x: x['count'])
                stats['insights'].append(
                    f"La majorité des éléments ({dominant_statut['count']}) ont le statut '{dominant_statut['statut']}'"
                )
            
            # Insight sur les tendances
            if hasattr(queryset.first(), 'date_creation'):
                recent_count = queryset.filter(
                    date_creation__gte=timezone.now() - timedelta(days=7)
                ).count()
                if recent_count > 0:
                    stats['insights'].append(
                        f"{recent_count} nouveaux éléments cette semaine"
                    )
        
        return stats
    
    def _get_suggestions(self, queryset, request):
        """Génère des suggestions intelligentes"""
        suggestions = {
            'sort_options': [
                {'value': 'relevance', 'label': 'Pertinence'},
                {'value': 'date', 'label': 'Date'},
                {'value': 'priority', 'label': 'Priorité'},
                {'value': 'value', 'label': 'Valeur'},
            ],
            'filter_options': [
                {'value': 'recent', 'label': 'Récents'},
                {'value': 'urgent', 'label': 'Urgents'},
                {'value': 'problematic', 'label': 'Problématiques'},
                {'value': 'high_value', 'label': 'Haute valeur'},
            ]
        }
        
        return suggestions


@login_required
def advanced_search_api(request):
    """
    API pour la recherche avancée en AJAX
    """
    if request.method == 'GET':
        search_query = request.GET.get('q', '')
        model_type = request.GET.get('model', 'propriete')
        
        # Sélection du modèle selon le type
        model_mapping = {
            'propriete': 'proprietes.models.Propriete',
            'contrat': 'contrats.models.Contrat',
            'paiement': 'paiements.models.Paiement',
            'utilisateur': 'utilisateurs.models.Utilisateur',
        }
        
        if model_type not in model_mapping:
            return JsonResponse({'error': 'Type de modèle invalide'}, status=400)
        
        # Import dynamique du modèle
        try:
            module_path, model_name = model_mapping[model_type].rsplit('.', 1)
            module = __import__(module_path, fromlist=[model_name])
            model_class = getattr(module, model_name)
        except ImportError:
            return JsonResponse({'error': 'Modèle non trouvé'}, status=400)
        
        # Analyse de la requête
        parsed_query = search_engine.parse_search_query(search_query)
        
        # Construction de la requête
        queryset = model_class.objects.all()
        if parsed_query:
            advanced_query = search_engine.build_advanced_query(
                model_class, parsed_query
            )
            queryset = queryset.filter(advanced_query)
        
        # Tri intelligent
        ordering = search_engine.get_smart_ordering(model_class, parsed_query)
        queryset = queryset.order_by(*ordering)
        
        # Suggestions
        suggestions = search_engine.get_search_suggestions(search_query, model_class)
        
        # Analytics
        analytics = search_engine.get_search_analytics(search_query)
        
        # Préparation des résultats
        results = []
        for obj in queryset[:10]:  # Limiter à 10 résultats
            results.append({
                'id': obj.id,
                'titre': getattr(obj, 'titre', str(obj)),
                'description': getattr(obj, 'description', ''),
                'url': obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else f'/{model_type}/{obj.id}/',
                'score': getattr(obj, 'relevance_score', 0),
            })
        
        response_data = {
            'query': search_query,
            'parsed_query': parsed_query,
            'results': results,
            'suggestions': suggestions,
            'analytics': analytics,
            'total_results': queryset.count(),
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def search_suggestions_api(request):
    """
    API pour les suggestions de recherche
    """
    query = request.GET.get('q', '')
    model_type = request.GET.get('model', 'propriete')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Sélection du modèle
    model_mapping = {
        'propriete': 'proprietes.models.Propriete',
        'contrat': 'contrats.models.Contrat',
        'paiement': 'paiements.models.Paiement',
        'utilisateur': 'utilisateurs.models.Utilisateur',
    }
    
    if model_type not in model_mapping:
        return JsonResponse({'suggestions': []})
    
    try:
        module_path, model_name = model_mapping[model_type].rsplit('.', 1)
        module = __import__(module_path, fromlist=[model_name])
        model_class = getattr(module, model_name)
    except ImportError:
        return JsonResponse({'suggestions': []})
    
    # Génération des suggestions
    suggestions = search_engine.get_search_suggestions(query, model_class)
    
    return JsonResponse({'suggestions': suggestions})


@login_required
def search_analytics_api(request):
    """
    API pour les analytics de recherche
    """
    query = request.GET.get('q', '')
    
    analytics = search_engine.get_search_analytics(query)
    
    # Ajout d'analytics supplémentaires
    analytics.update({
        'search_trends': _get_search_trends(),
        'popular_searches': _get_popular_searches(),
        'search_recommendations': _get_search_recommendations(query)
    })
    
    return JsonResponse(analytics)


def _get_search_trends():
    """Récupère les tendances de recherche"""
    # Simulation de tendances
    return {
        'trending_keywords': ['appartement', 'maison', 'studio', 'location'],
        'trending_cities': ['Paris', 'Lyon', 'Marseille', 'Bordeaux'],
        'trending_prices': ['500-800 XOF', '800-1200 XOF', '1200-2000 XOF']
    }


def _get_popular_searches():
    """Récupère les recherches populaires"""
    # Simulation de recherches populaires
    return [
        'appartement 2 pièces Paris',
        'maison avec jardin',
        'studio étudiant',
        'appartement de standing'
    ]


def _get_search_recommendations(query):
    """Génère des recommandations de recherche"""
    recommendations = []
    
    if 'appartement' in query.lower():
        recommendations.extend([
            'appartement 2 pièces',
            'appartement avec balcon',
            'appartement de standing'
        ])
    
    if 'maison' in query.lower():
        recommendations.extend([
            'maison avec jardin',
            'maison individuelle',
            'maison de ville'
        ])
    
    if any(word in query.lower() for word in ['étudiant', 'studio']):
        recommendations.extend([
            'studio meublé',
            'colocation',
            'logement étudiant'
        ])
    
    return recommendations[:5]  # Limiter à 5 recommandations 