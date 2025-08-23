"""
Moteur de recherche intelligent pour GESTIMMOB
Système hyper intelligent de recherche et de tri
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, F, Value, CharField, IntegerField, FloatField, Case, When
from django.db.models.functions import Concat, Coalesce, Cast
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class IntelligentSearchEngine:
    """
    Moteur de recherche intelligent avec fonctionnalités avancées
    """
    
    def __init__(self):
        self.search_history = {}
        self.search_patterns = {
            'prix': r'(\d+)\s*(XOF|francs?|cfa)',
            'surface': r'(\d+)\s*(m²|m2|mètres?\s*carrés?)',
            'ville': r'(à|dans|sur)\s+([A-Za-zÀ-ÿ\s]+)',
            'type': r'(appartement|maison|studio|loft|duplex|terrasse)',
            'statut': r'(disponible|loué|en\s+attente|réservé)',
            'urgence': r'(urgent|rapide|immédiat|dès\s+que\s+possible)',
        }
        
    def parse_search_query(self, query: str) -> Dict[str, Any]:
        """
        Analyse intelligente de la requête de recherche
        """
        if not query:
            return {}
            
        query = query.lower().strip()
        parsed = {
            'original': query,
            'keywords': [],
            'filters': {},
            'priority': 'normal',
            'semantic_meaning': self._extract_semantic_meaning(query)
        }
        
        # Extraction des mots-clés
        parsed['keywords'] = self._extract_keywords(query)
        
        # Extraction des filtres automatiques
        parsed['filters'] = self._extract_filters(query)
        
        # Détection de l'urgence
        if any(word in query for word in ['urgent', 'rapide', 'immédiat']):
            parsed['priority'] = 'high'
            
        return parsed
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés importants de la requête"""
        # Supprimer les mots vides
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'de', 'du', 'des',
            'à', 'au', 'aux', 'avec', 'sans', 'pour', 'par', 'dans', 'sur', 'sous',
            'entre', 'chez', 'vers', 'depuis', 'jusqu', 'pendant', 'avant', 'après',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'ce', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
            'son', 'sa', 'ses', 'notre', 'votre', 'leur', 'leurs'
        }
        
        words = re.findall(r'\b\w+\b', query)
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extrait automatiquement les filtres de la requête"""
        filters = {}
        
        # Recherche de prix
        prix_match = re.search(self.search_patterns['prix'], query)
        if prix_match:
            filters['prix_max'] = int(prix_match.group(1))
            
        # Recherche de surface
        surface_match = re.search(self.search_patterns['surface'], query)
        if surface_match:
            filters['surface_min'] = int(surface_match.group(1))
            
        # Recherche de ville
        ville_match = re.search(self.search_patterns['ville'], query)
        if ville_match:
            filters['ville'] = ville_match.group(2).strip()
            
        # Recherche de type
        type_match = re.search(self.search_patterns['type'], query)
        if type_match:
            filters['type'] = type_match.group(1)
            
        # Recherche de statut
        statut_match = re.search(self.search_patterns['statut'], query)
        if statut_match:
            filters['statut'] = statut_match.group(1)
            
        return filters
    
    def _extract_semantic_meaning(self, query: str) -> str:
        """Extrait le sens sémantique de la requête"""
        semantic_keywords = {
            'recherche': ['cherche', 'recherche', 'trouve', 'disponible'],
            'location': ['louer', 'location', 'bail', 'loyer'],
            'achat': ['acheter', 'achat', 'vendre', 'vente'],
            'urgence': ['urgent', 'rapide', 'immédiat', 'dès que possible'],
            'budget': ['pas cher', 'bon prix', 'économique', 'budget'],
            'luxe': ['luxueux', 'haut de gamme', 'premium', 'standing'],
            'famille': ['famille', 'enfants', 'grand', 'spacieux'],
            'étudiant': ['étudiant', 'petit', 'studio', 'économique'],
        }
        
        for category, keywords in semantic_keywords.items():
            if any(keyword in query for keyword in keywords):
                return category
                
        return 'general'
    
    def build_advanced_query(self, model_class, parsed_query: Dict[str, Any], 
                           additional_filters: Dict[str, Any] = None) -> Q:
        """
        Construit une requête avancée basée sur l'analyse de la recherche
        """
        query = Q()
        
        if not parsed_query:
            return query
            
        # Recherche par mots-clés
        if parsed_query.get('keywords'):
            keywords_query = Q()
            for keyword in parsed_query['keywords']:
                keywords_query |= self._build_keyword_query(model_class, keyword)
            query &= keywords_query
            
        # Filtres automatiques
        filters = parsed_query.get('filters', {})
        if additional_filters:
            filters.update(additional_filters)
            
        query &= self._build_filters_query(model_class, filters)
        
        return query
    
    def _build_keyword_query(self, model_class, keyword: str) -> Q:
        """Construit une requête pour un mot-clé"""
        # Déterminer les champs de recherche selon le modèle
        if hasattr(model_class, 'SEARCH_FIELDS'):
            search_fields = model_class.SEARCH_FIELDS
        else:
            # Champs par défaut selon le modèle
            search_fields = self._get_default_search_fields(model_class)
            
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": keyword})
            
        return query
    
    def _get_default_search_fields(self, model_class) -> List[str]:
        """Retourne les champs de recherche par défaut selon le modèle"""
        model_name = model_class.__name__.lower()
        
        field_mappings = {
            'propriete': ['titre', 'adresse', 'ville', 'notes'],
            'contrat': ['numero_contrat', 'propriete__titre', 'locataire__nom', 'locataire__prenom'],
            'paiement': ['contrat__propriete__titre', 'contrat__locataire__nom', 'contrat__locataire__prenom', 'notes'],
            'utilisateur': ['username', 'first_name', 'last_name', 'email'],
            'bailleur': ['nom', 'prenom', 'email', 'telephone'],
            'locataire': ['nom', 'prenom', 'email', 'telephone'],
        }
        
        return field_mappings.get(model_name, ['nom', 'titre', 'notes'])
    
    def _build_filters_query(self, model_class, filters: Dict[str, Any]) -> Q:
        """Construit une requête de filtres"""
        query = Q()
        
        for key, value in filters.items():
            if value is not None and value != '':
                if key == 'prix_max':
                    query &= Q(loyer_actuel__lte=value)
                elif key == 'prix_min':
                    query &= Q(loyer_actuel__gte=value)
                elif key == 'surface_min':
                    query &= Q(surface__gte=value)
                elif key == 'surface_max':
                    query &= Q(surface__lte=value)
                elif key == 'ville':
                    query &= Q(ville__icontains=value)
                elif key == 'type':
                    query &= Q(type_bien__nom__icontains=value)
                elif key == 'statut':
                    if value == 'disponible':
                        query &= Q(disponible=True)
                    elif value == 'loué':
                        query &= Q(disponible=False)
                elif key == 'date_debut':
                    query &= Q(date_creation__gte=value)
                elif key == 'date_fin':
                    query &= Q(date_creation__lte=value)
                else:
                    # Filtre générique
                    query &= Q(**{f"{key}__icontains": value})
                    
        return query
    
    def get_smart_ordering(self, model_class, parsed_query: Dict[str, Any], 
                          default_ordering: str = '-date_creation') -> List[str]:
        """
        Retourne un ordre de tri intelligent basé sur la requête
        """
        semantic_meaning = parsed_query.get('semantic_meaning', 'general')
        priority = parsed_query.get('priority', 'normal')
        
        # Ordre selon le sens sémantique
        semantic_ordering = {
            'urgence': ['-date_creation'],
            'budget': ['loyer_actuel'],
            'luxe': ['-loyer_actuel'],
            'famille': ['-surface', '-nombre_pieces'],
            'étudiant': ['loyer_actuel', 'surface'],
            'location': ['-date_creation', 'disponible'],
            'achat': ['-date_creation', 'prix_achat'],
        }
        
        ordering = semantic_ordering.get(semantic_meaning, [default_ordering])
        
        # Ajouter l'ordre de priorité si nécessaire
        if priority == 'high':
            ordering = ['-date_creation'] + ordering
            
        return ordering
    
    def get_search_suggestions(self, query: str, model_class) -> List[str]:
        """
        Génère des suggestions de recherche intelligentes
        """
        if not query or len(query) < 2:
            return []
            
        suggestions = []
        
        # Suggestions basées sur les données existantes
        try:
            # Villes
            villes = model_class.objects.values_list('ville', flat=True).distinct()
            suggestions.extend([f"à {ville}" for ville in villes if ville.lower().startswith(query.lower())])
            
            # Types
            if hasattr(model_class, 'type_bien'):
                types = model_class.objects.values_list('type_bien__nom', flat=True).distinct()
                suggestions.extend([f"{type_bien}" for type_bien in types if type_bien.lower().startswith(query.lower())])
                
            # Prix
            if any(char.isdigit() for char in query):
                suggestions.extend([f"{query} XOF", f"{query} francs CFA"])
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération des suggestions: {e}")
            
        return suggestions[:10]  # Limiter à 10 suggestions
    
    def get_search_analytics(self, query: str) -> Dict[str, Any]:
        """
        Analyse les tendances de recherche
        """
        analytics = {
            'query_length': len(query),
            'has_numbers': any(char.isdigit() for char in query),
            'has_special_chars': bool(re.search(r'[^a-zA-Z0-9\s]', query)),
            'word_count': len(query.split()),
            'estimated_complexity': 'simple'
        }
        
        # Complexité estimée
        if analytics['word_count'] > 5:
            analytics['estimated_complexity'] = 'complex'
        elif analytics['word_count'] > 2:
            analytics['estimated_complexity'] = 'medium'
            
        return analytics


class AdvancedSortingEngine:
    """
    Moteur de tri avancé avec algorithmes intelligents
    """
    
    def __init__(self):
        self.sorting_algorithms = {
            'relevance': self._sort_by_relevance,
            'smart_date': self._sort_by_smart_date,
            'priority_score': self._sort_by_priority_score,
            'multi_criteria': self._sort_by_multi_criteria,
        }
    
    def sort_queryset(self, queryset, sort_type: str = 'relevance', 
                     context: Dict[str, Any] = None) -> Any:
        """
        Trie un queryset avec un algorithme intelligent
        """
        if sort_type in self.sorting_algorithms:
            return self.sorting_algorithms[sort_type](queryset, context)
        else:
            return queryset.order_by('-date_creation')
    
    def _sort_by_relevance(self, queryset, context: Dict[str, Any] = None) -> Any:
        """
        Tri par pertinence basé sur plusieurs critères
        """
        if not context or 'search_query' not in context:
            return queryset.order_by('-date_creation')
            
        # Algorithme de scoring de pertinence adaptatif
        try:
            # Vérifier si le modèle a un champ priorite
            if hasattr(queryset.model, 'priorite'):
                queryset = queryset.annotate(
                    relevance_score=(
                        F('priorite') * 10 +
                        F('date_creation') * 0.1 +
                        Coalesce(F('loyer_actuel'), Value(0)) * 0.01
                    )
                ).order_by('-relevance_score')
            else:
                # Fallback pour les modèles sans priorite
                queryset = queryset.annotate(
                    relevance_score=(
                        F('date_creation') * 0.1 +
                        Coalesce(F('loyer_actuel'), Value(0)) * 0.01
                    )
                ).order_by('-relevance_score')
        except Exception:
            # Fallback simple si l'annotation échoue
            queryset = queryset.order_by('-date_creation')
        
        return queryset
    
    def _sort_by_smart_date(self, queryset, context: Dict[str, Any] = None) -> Any:
        """
        Tri intelligent par date avec prise en compte des événements
        """
        try:
            now = timezone.now()
            
            # Vérifier si le modèle a un champ date_creation
            if hasattr(queryset.model, 'date_creation'):
                queryset = queryset.annotate(
                    smart_date_score=(
                        # Bonus pour les éléments créés aujourd'hui
                        Case(
                            When(date_creation__date=now.date(), then=Value(100)),
                            default=Value(0)
                        )
                    )
                ).order_by('-smart_date_score', '-date_creation')
            else:
                # Fallback simple
                queryset = queryset.order_by('-date_creation')
        except Exception:
            queryset = queryset.order_by('-date_creation')
        
        return queryset
    
    def _sort_by_priority_score(self, queryset, context: Dict[str, Any] = None) -> Any:
        """
        Tri par score de priorité calculé
        """
        try:
            # Vérifier les champs disponibles
            has_priorite = hasattr(queryset.model, 'priorite')
            has_disponible = hasattr(queryset.model, 'disponible')
            has_statut = hasattr(queryset.model, 'statut')
            
            if has_priorite and has_disponible and has_statut:
                queryset = queryset.annotate(
                    priority_score=(
                        Coalesce(F('priorite'), Value(0)) * 100 +
                        Case(
                            When(disponible=True, then=Value(50)),
                            default=Value(0)
                        ) +
                        Case(
                            When(statut='urgent', then=Value(200)),
                            When(statut='important', then=Value(100)),
                            default=Value(0)
                        )
                    )
                ).order_by('-priority_score')
            elif has_disponible:
                queryset = queryset.annotate(
                    priority_score=(
                        Case(
                            When(disponible=True, then=Value(50)),
                            default=Value(0)
                        )
                    )
                ).order_by('-priority_score')
            else:
                queryset = queryset.order_by('-date_creation')
        except Exception:
            queryset = queryset.order_by('-date_creation')
        
        return queryset
    
    def _sort_by_multi_criteria(self, queryset, context: Dict[str, Any] = None) -> Any:
        """
        Tri multi-critères avec pondération
        """
        try:
            weights = context.get('weights', {
                'date': 0.3,
                'priority': 0.4,
                'relevance': 0.3
            })
            
            # Vérifier les champs disponibles
            has_priorite = hasattr(queryset.model, 'priorite')
            has_loyer = hasattr(queryset.model, 'loyer_actuel')
            has_date = hasattr(queryset.model, 'date_creation')
            
            if has_date and has_priorite and has_loyer:
                queryset = queryset.annotate(
                    multi_score=(
                        F('date_creation') * weights['date'] +
                        Coalesce(F('priorite'), Value(0)) * weights['priority'] +
                        Coalesce(F('loyer_actuel'), Value(0)) * weights['relevance']
                    )
                ).order_by('-multi_score')
            elif has_date and has_loyer:
                queryset = queryset.annotate(
                    multi_score=(
                        F('date_creation') * weights['date'] +
                        Coalesce(F('loyer_actuel'), Value(0)) * weights['relevance']
                    )
                ).order_by('-multi_score')
            else:
                queryset = queryset.order_by('-date_creation')
        except Exception:
            queryset = queryset.order_by('-date_creation')
        
        return queryset


class SearchFilterBuilder:
    """
    Constructeur de filtres de recherche avancés
    """
    
    def __init__(self):
        self.filter_templates = {
            'date_range': self._build_date_range_filter,
            'price_range': self._build_price_range_filter,
            'location_filter': self._build_location_filter,
            'status_filter': self._build_status_filter,
            'custom_filter': self._build_custom_filter,
        }
    
    def build_filter(self, filter_type: str, **kwargs) -> Q:
        """
        Construit un filtre selon le type spécifié
        """
        if filter_type in self.filter_templates:
            return self.filter_templates[filter_type](**kwargs)
        else:
            return Q()
    
    def _build_date_range_filter(self, **kwargs) -> Q:
        """Filtre par plage de dates"""
        date_debut = kwargs.get('date_debut')
        date_fin = kwargs.get('date_fin')
        field = kwargs.get('field', 'date_creation')
        
        query = Q()
        if date_debut:
            query &= Q(**{f"{field}__gte": date_debut})
        if date_fin:
            query &= Q(**{f"{field}__lte": date_fin})
            
        return query
    
    def _build_price_range_filter(self, **kwargs) -> Q:
        """Filtre par plage de prix"""
        prix_min = kwargs.get('prix_min')
        prix_max = kwargs.get('prix_max')
        
        query = Q()
        if prix_min is not None:
            query &= (Q(loyer_actuel__gte=prix_min) | Q(prix_location__gte=prix_min))
        if prix_max is not None:
            query &= (Q(loyer_actuel__lte=prix_max) | Q(prix_location__lte=prix_max))
            
        return query
    
    def _build_location_filter(self, **kwargs) -> Q:
        """Filtre par localisation"""
        ville = kwargs.get('ville')
        code_postal = kwargs.get('code_postal')
        rayon = kwargs.get('rayon')  # Rayon de recherche en km
        
        query = Q()
        if ville:
            query &= Q(ville__icontains=ville)
        if code_postal:
            query &= Q(code_postal__icontains=code_postal)
            
        return query
    
    def _build_status_filter(self, **kwargs) -> Q:
        """Filtre par statut"""
        statut = kwargs.get('statut')
        disponible = kwargs.get('disponible')
        
        query = Q()
        if statut:
            query &= Q(statut=statut)
        if disponible is not None:
            query &= Q(disponible=disponible)
            
        return query
    
    def _build_custom_filter(self, **kwargs) -> Q:
        """Filtre personnalisé"""
        field = kwargs.get('field')
        value = kwargs.get('value')
        operator = kwargs.get('operator', 'exact')
        
        if not field or value is None:
            return Q()
            
        if operator == 'contains':
            return Q(**{f"{field}__icontains": value})
        elif operator == 'startswith':
            return Q(**{f"{field}__startswith": value})
        elif operator == 'endswith':
            return Q(**{f"{field}__endswith": value})
        elif operator == 'gte':
            return Q(**{f"{field}__gte": value})
        elif operator == 'lte':
            return Q(**{f"{field}__lte": value})
        else:
            return Q(**{field: value})


# Instances globales
search_engine = IntelligentSearchEngine()
sorting_engine = AdvancedSortingEngine()
filter_builder = SearchFilterBuilder() 