"""
Vues intelligentes pour les listes déroulantes avec recherche et tri
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
import json
from django.utils import timezone
from django.urls import reverse


class IntelligentListView(ListView):
    """
    Vue de liste intelligente avec recherche, filtres et tri
    """
    
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtenir le queryset avec filtres et tri"""
        queryset = self.model.objects.all()
        
        # Recherche
        search = self.request.GET.get('search', '')
        if search:
            queryset = self.apply_search(queryset, search)
        
        # Filtres
        queryset = self.apply_filters(queryset)
        
        # Tri
        queryset = self.apply_sorting(queryset)
        
        return queryset
    
    def apply_search(self, queryset, search):
        """Appliquer la recherche"""
        if hasattr(self, 'search_fields'):
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search})
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
        sort_field = self.request.GET.get('sort', self.default_sort)
        order = self.request.GET.get('order', 'asc')
        
        if sort_field:
            if order == 'desc':
                sort_field = f'-{sort_field}'
            queryset = queryset.order_by(sort_field)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Obtenir le contexte avec données intelligentes"""
        context = super().get_context_data(**kwargs)
        
        # Configuration de la page
        add_url_name = getattr(self, 'add_url', None)
        add_url = None
        if add_url_name:
            try:
                add_url = reverse(add_url_name)
            except:
                add_url = None
                
        context.update({
            'page_title': getattr(self, 'page_title', 'Liste Intelligente'),
            'page_icon': getattr(self, 'page_icon', 'list'),
            'add_url': add_url,
            'add_text': getattr(self, 'add_text', 'Ajouter'),
            'export_url': getattr(self, 'export_url', None),
            'empty_icon': getattr(self, 'empty_icon', 'inbox'),
            'empty_title': getattr(self, 'empty_title', 'Aucun élément trouvé'),
            'empty_message': getattr(self, 'empty_message', 'Aucun élément ne correspond aux critères de recherche.'),
            'enable_realtime': getattr(self, 'enable_realtime', False),
        })
        
        # Statistiques
        context['stats'] = self.get_statistics()
        
        # Suggestions intelligentes
        context['suggestions'] = self.get_suggestions()
        
        # Colonnes du tableau
        context['columns'] = self.get_columns()
        
        # Actions
        context['actions'] = self.get_actions()
        
        # Filtres
        context['filters'] = self.get_filters()
        
        # Options de tri
        context['sort_options'] = self.get_sort_options()
        
        return context
    
    def get_statistics(self):
        """Obtenir les statistiques"""
        queryset = self.get_queryset()
        
        stats = []
        
        # Statistiques de base
        stats.append({
            'label': 'Total',
            'value': queryset.count()
        })
        
        # Statistiques spécifiques au modèle
        if hasattr(self, 'get_custom_statistics'):
            stats.extend(self.get_custom_statistics(queryset))
        
        return stats
    
    def get_suggestions(self):
        """Obtenir les suggestions intelligentes"""
        suggestions = []
        
        # Suggestions basées sur les données
        queryset = self.get_queryset()
        
        if queryset.count() == 0:
            suggestions.append("Aucune donnée trouvée. Essayez de modifier vos critères de recherche.")
        
        # Suggestions spécifiques
        if hasattr(self, 'get_custom_suggestions'):
            suggestions.extend(self.get_custom_suggestions(queryset))
        
        return suggestions
    
    def get_columns(self):
        """Obtenir les colonnes du tableau"""
        return getattr(self, 'columns', [])
    
    def get_actions(self):
        """Obtenir les actions disponibles"""
        return getattr(self, 'actions', [])
    
    def get_filters(self):
        """Obtenir les filtres disponibles"""
        filters = []
        
        if hasattr(self, 'filter_fields'):
            for field_name in self.filter_fields:
                filter_config = self.get_filter_config(field_name)
                if filter_config:
                    filters.append(filter_config)
        
        return filters
    
    def get_filter_config(self, field_name):
        """Obtenir la configuration d'un filtre"""
        # Configuration par défaut
        config = {
            'name': field_name,
            'label': field_name.replace('_', ' ').title(),
            'options': []
        }
        
        # Options spécifiques au champ
        if hasattr(self, f'get_{field_name}_options'):
            config['options'] = getattr(self, f'get_{field_name}_options')()
        
        return config
    
    def get_sort_options(self):
        """Obtenir les options de tri"""
        return getattr(self, 'sort_options', [])


# Vues spécifiques pour chaque modèle

class IntelligentProprieteListView(IntelligentListView):
    """Vue intelligente pour les propriétés"""
    
    from proprietes.models import Propriete
    model = Propriete
    
    page_title = "Liste des Propriétés"
    page_icon = "house"
    add_url = "proprietes:ajouter"
    add_text = "Ajouter une Propriété"
    
    search_fields = ['titre', 'adresse', 'ville', 'code_postal']
    filter_fields = ['type_bien', 'ville', 'disponible', 'etat']
    default_sort = 'ville'
    
    columns = [
        {'field': 'titre', 'label': 'Propriété', 'sortable': True},
        {'field': 'adresse', 'label': 'Adresse', 'sortable': True},
        {'field': 'ville', 'label': 'Ville', 'sortable': True},
        {'field': 'loyer_actuel', 'label': 'Loyer', 'sortable': True},
        {'field': 'disponible', 'label': 'Disponible', 'sortable': True},
        {'field': 'etat', 'label': 'État', 'sortable': True},
    ]
    
    actions = [
        {'url_name': 'proprietes:detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'proprietes:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    
    sort_options = [
        {'value': 'ville', 'label': 'Ville'},
        {'value': 'loyer_actuel', 'label': 'Loyer'},
        {'value': 'surface', 'label': 'Surface'},
        {'value': 'date_creation', 'label': 'Date de création'},
    ]
    
    def get_custom_statistics(self, queryset):
        """Statistiques spécifiques aux propriétés"""
        return [
            {
                'label': 'Louées',
                'value': queryset.filter(disponible=False).count()
            },
            {
                'label': 'Disponibles',
                'value': queryset.filter(disponible=True).count()
            },
            {
                'label': 'Revenus totaux',
                'value': f"{queryset.filter(disponible=False).aggregate(Sum('loyer_actuel'))['loyer_actuel__sum'] or 0} F CFA"
            }
        ]
    
    def get_type_bien_options(self):
        """Options pour le filtre type de bien"""
        from proprietes.models import TypeBien
        return [{'value': tb.id, 'label': tb.nom} for tb in TypeBien.objects.all()]
    
    def get_ville_options(self):
        """Options pour le filtre ville"""
        return [{'value': ville, 'label': ville} for ville in self.model.objects.values_list('ville', flat=True).distinct()]


class IntelligentContratListView(IntelligentListView):
    """Vue intelligente pour les contrats"""
    
    from contrats.models import Contrat
    model = Contrat
    
    page_title = "Liste des Contrats"
    page_icon = "file-earmark-text"
    add_url = "contrats:ajouter"
    add_text = "Ajouter un Contrat"
    
    search_fields = ['reference', 'propriete__titre', 'locataire__nom', 'locataire__prenom']
    filter_fields = ['statut', 'propriete__ville']
    default_sort = 'date_debut'
    
    columns = [
        {'field': 'reference', 'label': 'Référence', 'sortable': True},
        {'field': 'propriete__titre', 'label': 'Propriété', 'sortable': True},
        {'field': 'locataire__nom', 'label': 'Locataire', 'sortable': True},
        {'field': 'date_debut', 'label': 'Date Début', 'sortable': True},
        {'field': 'date_fin', 'label': 'Date Fin', 'sortable': True},
        {'field': 'loyer_mensuel', 'label': 'Loyer', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
    ]
    
    actions = [
        {'url_name': 'contrats:detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'contrats:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    
    sort_options = [
        {'value': 'date_debut', 'label': 'Date de début'},
        {'value': 'date_fin', 'label': 'Date de fin'},
        {'value': 'loyer_mensuel', 'label': 'Loyer'},
        {'value': 'reference', 'label': 'Référence'},
    ]
    
    def get_custom_statistics(self, queryset):
        """Statistiques spécifiques aux contrats"""
        return [
            {
                'label': 'Actifs',
                'value': queryset.filter(statut='actif').count()
            },
            {
                'label': 'Expirés',
                'value': queryset.filter(statut='expire').count()
            },
            {
                'label': 'Loyer moyen',
                'value': f"{queryset.aggregate(Avg('loyer_mensuel'))['loyer_mensuel__avg'] or 0:.0f} F CFA"
            }
        ]


class IntelligentPaiementListView(IntelligentListView):
    """Vue intelligente pour les paiements"""
    
    from paiements.models import Paiement
    model = Paiement
    
    page_title = "Liste des Paiements"
    page_icon = "cash-coin"
    add_url = "paiements:ajouter"
    add_text = "Ajouter un Paiement"
    
    search_fields = ['reference', 'contrat__locataire__nom', 'contrat__propriete__titre']
    filter_fields = ['statut', 'type_paiement', 'methode_paiement']
    default_sort = 'date_paiement'
    
    columns = [
        {'field': 'reference', 'label': 'Référence', 'sortable': True},
        {'field': 'contrat__reference', 'label': 'Contrat', 'sortable': True},
        {'field': 'contrat__locataire__nom', 'label': 'Locataire', 'sortable': True},
        {'field': 'montant', 'label': 'Montant', 'sortable': True},
        {'field': 'date_paiement', 'label': 'Date', 'sortable': True},
        {'field': 'methode_paiement', 'label': 'Méthode', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
    ]
    
    actions = [
        {'url_name': 'paiements:detail_paiement', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'paiements:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    
    sort_options = [
        {'value': 'date_paiement', 'label': 'Date de paiement'},
        {'value': 'montant', 'label': 'Montant'},
        {'value': 'reference', 'label': 'Référence'},
    ]
    
    def get_custom_statistics(self, queryset):
        """Statistiques spécifiques aux paiements"""
        return [
            {
                'label': 'Validés',
                'value': queryset.filter(statut='valide').count()
            },
            {
                'label': 'En attente',
                'value': queryset.filter(est_valide=False).count()
            },
            {
                'label': 'Total perçu',
                'value': f"{queryset.filter(statut='valide').aggregate(Sum('montant'))['montant__sum'] or 0} F CFA"
            }
        ]


class IntelligentUtilisateurListView(IntelligentListView):
    """Vue intelligente pour les utilisateurs"""
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    model = User
    
    page_title = "Liste des Utilisateurs"
    page_icon = "person-gear"
    add_url = "utilisateurs:ajouter_utilisateur"
    add_text = "Ajouter un Utilisateur"
    
    search_fields = ['username', 'first_name', 'last_name', 'email']
    filter_fields = ['is_active', 'groups']
    default_sort = 'username'
    
    columns = [
        {'field': 'username', 'label': 'Nom d\'utilisateur', 'sortable': True},
        {'field': 'first_name', 'label': 'Prénom', 'sortable': True},
        {'field': 'last_name', 'label': 'Nom', 'sortable': True},
        {'field': 'email', 'label': 'Email', 'sortable': True},
        {'field': 'is_active', 'label': 'Actif', 'sortable': True},
        {'field': 'date_joined', 'label': 'Date d\'inscription', 'sortable': True},
    ]
    
    actions = [
        {'url_name': 'utilisateurs:detail_utilisateur', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'utilisateurs:modifier_utilisateur', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    
    sort_options = [
        {'value': 'username', 'label': 'Nom d\'utilisateur'},
        {'value': 'last_name', 'label': 'Nom'},
        {'value': 'date_joined', 'label': 'Date d\'inscription'},
    ]
    
    def get_custom_statistics(self, queryset):
        """Statistiques spécifiques aux utilisateurs"""
        return [
            {
                'label': 'Actifs',
                'value': queryset.filter(is_active=True).count()
            },
            {
                'label': 'Inactifs',
                'value': queryset.filter(is_active=False).count()
            },
            {
                'label': 'Nouveaux ce mois',
                'value': queryset.filter(date_joined__month=timezone.now().month).count()
            }
        ]


# Vues AJAX pour les mises à jour en temps réel

@login_required
@csrf_exempt
def ajax_update_list(request, model_name):
    """Mise à jour AJAX d'une liste"""
    try:
        # Mapper le nom du modèle à la vue
        view_mapping = {
            'proprietes': IntelligentProprieteListView,
            'contrats': IntelligentContratListView,
            'paiements': IntelligentPaiementListView,
            'utilisateurs': IntelligentUtilisateurListView,
        }
        
        if model_name not in view_mapping:
            return JsonResponse({'error': 'Modèle non supporté'}, status=400)
        
        # Créer la vue et obtenir les données
        view_class = view_mapping[model_name]
        view = view_class()
        view.request = request
        view.kwargs = {}
        
        # Obtenir le contexte
        context = view.get_context_data()
        
        # Retourner les données
        return JsonResponse({
            'success': True,
            'stats': context['stats'],
            'suggestions': context['suggestions'],
            'total_count': context['object_list'].count(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ajax_search(request, model_name):
    """Recherche AJAX"""
    try:
        search_term = request.GET.get('q', '')
        
        # Mapper le nom du modèle
        model_mapping = {
            'proprietes': 'proprietes.models.Propriete',
            'contrats': 'contrats.models.Contrat',
            'paiements': 'paiements.models.Paiement',
            'utilisateurs': 'django.contrib.auth.models.User',
        }
        
        if model_name not in model_mapping:
            return JsonResponse({'error': 'Modèle non supporté'}, status=400)
        
        # Importer le modèle
        module_path, model_class_name = model_mapping[model_name].rsplit('.', 1)
        module = __import__(module_path, fromlist=[model_class_name])
        model = getattr(module, model_class_name)
        
        # Recherche
        results = []
        if search_term:
            # Recherche simple par nom/titre
            if model_name == 'proprietes':
                queryset = model.objects.filter(
                    Q(titre__icontains=search_term) |
                    Q(ville__icontains=search_term)
                )[:10]
            elif model_name == 'contrats':
                queryset = model.objects.filter(
                    Q(reference__icontains=search_term) |
                    Q(propriete__titre__icontains=search_term)
                )[:10]
            elif model_name == 'paiements':
                queryset = model.objects.filter(
                    Q(reference__icontains=search_term) |
                    Q(contrat__locataire__nom__icontains=search_term)
                )[:10]
            elif model_name == 'utilisateurs':
                queryset = model.objects.filter(
                    Q(username__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term)
                )[:10]
            
            for obj in queryset:
                results.append({
                    'id': obj.id,
                    'text': str(obj),
                    'url': f'/{model_name}/{obj.id}/'
                })
        
        return JsonResponse({'results': results})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500) 