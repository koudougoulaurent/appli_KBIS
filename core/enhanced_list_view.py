"""
Vue de liste améliorée avec recherche intelligente
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .enhanced_search import EnhancedSearchService


class EnhancedListView(ListView):
    """
    Vue de liste améliorée avec recherche intelligente
    """
    
    template_name = 'base_liste_enhanced.html'
    paginate_by = 20
    search_service = EnhancedSearchService()
    
    def get_queryset(self):
        """Obtenir le queryset avec recherche et filtres"""
        queryset = self.model.objects.all()
        
        # Recherche intelligente
        search_term = self.request.GET.get('search', '').strip()
        if search_term:
            queryset = self.apply_enhanced_search(queryset, search_term)
        
        # Filtres
        queryset = self.apply_filters(queryset)
        
        # Tri
        queryset = self.apply_sorting(queryset)
        
        return queryset
    
    def apply_enhanced_search(self, queryset, search_term):
        """Appliquer la recherche intelligente"""
        model_name = self.model.__name__.lower()
        
        if model_name == 'bailleur':
            return self.search_service.search_bailleurs(queryset, search_term)
        elif model_name == 'locataire':
            return self.search_service.search_locataires(queryset, search_term)
        elif model_name == 'propriete':
            return self.search_service.search_proprietes(queryset, search_term)
        elif model_name == 'contrat':
            return self.search_service.search_contrats(queryset, search_term)
        elif model_name == 'paiement':
            return self.search_service.search_paiements(queryset, search_term)
        elif model_name == 'retraitbailleur':
            return self.search_service.search_retraits(queryset, search_term)
        else:
            # Recherche générique
            return self.apply_generic_search(queryset, search_term)
    
    def apply_generic_search(self, queryset, search_term):
        """Recherche générique pour les modèles non spécifiés"""
        if hasattr(self, 'search_fields'):
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_term})
            queryset = queryset.filter(q_objects)
        return queryset
    
    def apply_filters(self, queryset):
        """Appliquer les filtres"""
        if hasattr(self, 'filter_fields'):
            for field_name in self.filter_fields:
                value = self.request.GET.get(field_name)
                if value:
                    queryset = queryset.filter(**{field_name: value})
        return queryset
    
    def apply_sorting(self, queryset):
        """Appliquer le tri"""
        sort_field = self.request.GET.get('sort', getattr(self, 'default_sort', None))
        if sort_field:
            queryset = queryset.order_by(sort_field)
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajouter des données au contexte"""
        context = super().get_context_data(**kwargs)
        
        # Terme de recherche
        context['search_term'] = self.request.GET.get('search', '')
        
        # Suggestions de recherche
        search_term = context['search_term']
        if search_term:
            model_name = self.model.__name__.lower()
            context['search_suggestions'] = self.search_service.get_search_suggestions(model_name, search_term)
        
        # Statistiques
        context.update(self.get_statistics())
        
        # Filtres disponibles
        context['available_filters'] = self.get_available_filters()
        
        return context
    
    def get_statistics(self):
        """Obtenir les statistiques"""
        stats = {}
        
        # Statistiques de base
        stats['total_count'] = self.model.objects.count()
        stats['filtered_count'] = self.get_queryset().count()
        
        # Statistiques spécifiques au modèle
        if hasattr(self, 'get_model_statistics'):
            stats.update(self.get_model_statistics())
        
        return stats
    
    def get_available_filters(self):
        """Obtenir les filtres disponibles"""
        filters = {}
        
        if hasattr(self, 'filter_fields'):
            for field_name in self.filter_fields:
                if hasattr(self.model, field_name):
                    field = self.model._meta.get_field(field_name)
                    if hasattr(field, 'choices') and field.choices:
                        filters[field_name] = field.choices
                    else:
                        # Pour les champs sans choix, récupérer les valeurs uniques
                        values = self.model.objects.values_list(field_name, flat=True).distinct()
                        filters[field_name] = [(v, v) for v in values if v]
        
        return filters


class EnhancedSearchMixin:
    """
    Mixin pour ajouter la recherche améliorée à n'importe quelle vue
    """
    
    def get_queryset(self):
        """Appliquer la recherche améliorée"""
        queryset = super().get_queryset()
        
        search_term = self.request.GET.get('search', '').strip()
        if search_term:
            model_name = self.model.__name__.lower()
            search_service = EnhancedSearchService()
            
            if model_name == 'bailleur':
                queryset = search_service.search_bailleurs(queryset, search_term)
            elif model_name == 'locataire':
                queryset = search_service.search_locataires(queryset, search_term)
            elif model_name == 'propriete':
                queryset = search_service.search_proprietes(queryset, search_term)
            elif model_name == 'contrat':
                queryset = search_service.search_contrats(queryset, search_term)
            elif model_name == 'paiement':
                queryset = search_service.search_paiements(queryset, search_term)
            elif model_name == 'retraitbailleur':
                queryset = search_service.search_retraits(queryset, search_term)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajouter les données de recherche au contexte"""
        context = super().get_context_data(**kwargs)
        
        # Terme de recherche
        context['search_term'] = self.request.GET.get('search', '')
        
        # Suggestions de recherche
        search_term = context['search_term']
        if search_term:
            model_name = self.model.__name__.lower()
            search_service = EnhancedSearchService()
            context['search_suggestions'] = search_service.get_search_suggestions(model_name, search_term)
        
        return context


class AjaxSearchView:
    """
    Vue AJAX pour la recherche en temps réel
    """
    
    def get(self, request):
        """Recherche AJAX"""
        search_term = request.GET.get('q', '').strip()
        model_name = request.GET.get('model', '')
        
        if not search_term or len(search_term) < 2:
            return JsonResponse({'results': [], 'suggestions': []})
        
        # Obtenir le modèle
        model = self.get_model_by_name(model_name)
        if not model:
            return JsonResponse({'error': 'Modèle non trouvé'}, status=400)
        
        # Recherche
        search_service = EnhancedSearchService()
        queryset = model.objects.all()
        
        if model_name == 'bailleur':
            queryset = search_service.search_bailleurs(queryset, search_term)
        elif model_name == 'locataire':
            queryset = search_service.search_locataires(queryset, search_term)
        elif model_name == 'propriete':
            queryset = search_service.search_proprietes(queryset, search_term)
        elif model_name == 'contrat':
            queryset = search_service.search_contrats(queryset, search_term)
        elif model_name == 'paiement':
            queryset = search_service.search_paiements(queryset, search_term)
        
        # Limiter les résultats
        results = queryset[:10]
        
        # Formater les résultats
        formatted_results = []
        for obj in results:
            formatted_results.append({
                'id': obj.id,
                'text': str(obj),
                'url': self.get_object_url(obj, model_name)
            })
        
        # Suggestions
        suggestions = search_service.get_search_suggestions(model_name, search_term)
        
        return JsonResponse({
            'results': formatted_results,
            'suggestions': suggestions
        })
    
    def get_model_by_name(self, model_name):
        """Obtenir le modèle par nom"""
        from proprietes.models import Bailleur, Locataire, Propriete
        from contrats.models import Contrat
        from paiements.models import Paiement, RetraitBailleur
        
        models = {
            'bailleur': Bailleur,
            'locataire': Locataire,
            'propriete': Propriete,
            'contrat': Contrat,
            'paiement': Paiement,
            'retrait': RetraitBailleur,
        }
        
        return models.get(model_name)
    
    def get_object_url(self, obj, model_name):
        """Obtenir l'URL de l'objet"""
        from django.urls import reverse
        
        url_mapping = {
            'bailleur': 'proprietes:detail_bailleur',
            'locataire': 'proprietes:detail_locataire',
            'propriete': 'proprietes:detail',
            'contrat': 'contrats:detail',
            'paiement': 'paiements:detail',
            'retrait': 'paiements:detail_retrait',
        }
        
        url_name = url_mapping.get(model_name)
        if url_name:
            try:
                return reverse(url_name, args=[obj.id])
            except:
                pass
        
        return '#'
