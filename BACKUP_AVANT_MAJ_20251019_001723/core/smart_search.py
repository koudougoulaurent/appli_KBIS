"""
Système de recherche intelligente et contextuelle
Recherche unifiée à travers tous les modules
"""

from django.db.models import Q, Count
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import re

User = get_user_model()

class SmartSearchSystem:
    """
    Système de recherche intelligente qui comprend le contexte
    """
    
    @staticmethod
    def search_all_modules(query, request, limit=10):
        """
        Recherche unifiée dans tous les modules
        """
        cache_key = f"smart_search_{hash(query)}_{request.user.pk}"
        cached_results = cache.get(cache_key)
        
        if cached_results is not None:
            return cached_results
            
        results = {
            'proprietes': [],
            'bailleurs': [],
            'locataires': [],
            'contrats': [],
            'paiements': [],
            'suggestions': [],
            'total': 0
        }
        
        # Recherche dans les propriétés
        results['proprietes'] = SmartSearchSystem._search_proprietes(query, limit)
        
        # Recherche dans les bailleurs
        results['bailleurs'] = SmartSearchSystem._search_bailleurs(query, limit)
        
        # Recherche dans les locataires
        results['locataires'] = SmartSearchSystem._search_locataires(query, limit)
        
        # Recherche dans les contrats
        results['contrats'] = SmartSearchSystem._search_contrats(query, limit)
        
        # Recherche dans les paiements
        results['paiements'] = SmartSearchSystem._search_paiements(query, limit)
        
        # Suggestions intelligentes
        results['suggestions'] = SmartSearchSystem._get_suggestions(query, request)
        
        # Calcul du total
        results['total'] = sum(len(v) for k, v in results.items() if k != 'suggestions')
        
        # Cache pour 5 minutes
        cache.set(cache_key, results, 300)
        return results
    
    @staticmethod
    def _search_proprietes(query, limit):
        """Recherche dans les propriétés"""
        try:
            from proprietes.models import Propriete
            
            # Recherche par numéro, adresse, type
            proprietes = Propriete.objects.filter(
                Q(numero_propriete__icontains=query) |
                Q(adresse__icontains=query) |
                Q(ville__icontains=query) |
                Q(type_propriete__icontains=query),
                is_deleted=False
            ).select_related('bailleur')[:limit]
            
            return [
                {
                    'id': p.pk,
                    'type': 'propriete',
                    'title': f"Propriété {p.numero_propriete}",
                    'subtitle': f"{p.adresse}, {p.ville}",
                    'url': f"/proprietes/detail/{p.pk}/",
                    'icon': 'house',
                    'badge': p.type_propriete,
                    'bailleur': p.bailleur.get_nom_complet() if p.bailleur else 'Sans bailleur'
                }
                for p in proprietes
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def _search_bailleurs(query, limit):
        """Recherche dans les bailleurs"""
        try:
            from proprietes.models import Bailleur
            
            bailleurs = Bailleur.objects.filter(
                Q(nom__icontains=query) |
                Q(prenom__icontains=query) |
                Q(telephone__icontains=query) |
                Q(email__icontains=query),
                is_deleted=False
            )[:limit]
            
            return [
                {
                    'id': b.pk,
                    'type': 'bailleur',
                    'title': b.get_nom_complet(),
                    'subtitle': f"{b.telephone} • {b.email or 'Pas d\'email'}",
                    'url': f"/proprietes/bailleurs/{b.pk}/",
                    'icon': 'person-badge',
                    'badge': 'Bailleur'
                }
                for b in bailleurs
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def _search_locataires(query, limit):
        """Recherche dans les locataires"""
        try:
            from proprietes.models import Locataire
            
            locataires = Locataire.objects.filter(
                Q(nom__icontains=query) |
                Q(prenom__icontains=query) |
                Q(telephone__icontains=query) |
                Q(email__icontains=query),
                is_deleted=False
            )[:limit]
            
            return [
                {
                    'id': l.pk,
                    'type': 'locataire',
                    'title': l.get_nom_complet(),
                    'subtitle': f"{l.telephone} • {l.email or 'Pas d\'email'}",
                    'url': f"/proprietes/locataires/{l.pk}/",
                    'icon': 'person',
                    'badge': 'Locataire'
                }
                for l in locataires
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def _search_contrats(query, limit):
        """Recherche dans les contrats"""
        try:
            from contrats.models import Contrat
            
            contrats = Contrat.objects.filter(
                Q(numero_contrat__icontains=query) |
                Q(locataire__nom__icontains=query) |
                Q(locataire__prenom__icontains=query) |
                Q(propriete__numero_propriete__icontains=query),
                is_deleted=False
            ).select_related('locataire', 'propriete')[:limit]
            
            return [
                {
                    'id': c.pk,
                    'type': 'contrat',
                    'title': f"Contrat {c.numero_contrat}",
                    'subtitle': f"{c.locataire.get_nom_complet()} • {c.propriete.numero_propriete}",
                    'url': f"/contrats/detail/{c.pk}/",
                    'icon': 'file-text',
                    'badge': c.get_statut_display(),
                    'montant': f"{c.montant_loyer} F CFA"
                }
                for c in contrats
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def _search_paiements(query, limit):
        """Recherche dans les paiements"""
        try:
            from paiements.models import Paiement
            
            paiements = Paiement.objects.filter(
                Q(reference_paiement__icontains=query) |
                Q(contrat__numero_contrat__icontains=query) |
                Q(contrat__locataire__nom__icontains=query) |
                Q(contrat__locataire__prenom__icontains=query),
                is_deleted=False
            ).select_related('contrat__locataire')[:limit]
            
            return [
                {
                    'id': p.pk,
                    'type': 'paiement',
                    'title': f"Paiement {p.reference_paiement or p.pk}",
                    'subtitle': f"{p.contrat.locataire.get_nom_complet()} • {p.montant} F CFA",
                    'url': f"/paiements/detail/{p.pk}/",
                    'icon': 'credit-card',
                    'badge': p.get_statut_display(),
                    'date': p.date_paiement.strftime('%d/%m/%Y')
                }
                for p in paiements
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def _get_suggestions(query, request):
        """Suggestions intelligentes basées sur la requête"""
        suggestions = []
        
        # Détection de type de recherche
        if re.match(r'^[A-Z0-9-]+$', query):
            # Probablement un numéro de propriété ou contrat
            suggestions.append({
                'type': 'numero',
                'label': f'Rechercher le numéro "{query}"',
                'icon': 'search',
                'action': 'search_numero'
            })
        
        if '@' in query:
            # Probablement un email
            suggestions.append({
                'type': 'email',
                'label': f'Rechercher l\'email "{query}"',
                'icon': 'envelope',
                'action': 'search_email'
            })
        
        if re.match(r'^[0-9+\-\s]+$', query):
            # Probablement un téléphone
            suggestions.append({
                'type': 'telephone',
                'label': f'Rechercher le téléphone "{query}"',
                'icon': 'phone',
                'action': 'search_telephone'
            })
        
        # Suggestions contextuelles
        suggestions.extend([
            {
                'type': 'action',
                'label': f'Ajouter "{query}" comme nouvelle propriété',
                'icon': 'plus-circle',
                'action': 'add_propriete'
            },
            {
                'type': 'action',
                'label': f'Ajouter "{query}" comme nouveau bailleur',
                'icon': 'person-plus',
                'action': 'add_bailleur'
            }
        ])
        
        return suggestions
    
    @staticmethod
    def get_recent_searches(request, limit=5):
        """Récupère les recherches récentes de l'utilisateur"""
        cache_key = f"recent_searches_{request.user.pk}"
        return cache.get(cache_key, [])
    
    @staticmethod
    def save_search(request, query):
        """Sauvegarde une recherche dans l'historique"""
        cache_key = f"recent_searches_{request.user.pk}"
        recent_searches = cache.get(cache_key, [])
        
        # Ajouter la nouvelle recherche
        recent_searches.insert(0, {
            'query': query,
            'timestamp': timezone.now().isoformat()
        })
        
        # Garder seulement les 10 dernières
        recent_searches = recent_searches[:10]
        
        # Sauvegarder pour 24h
        cache.set(cache_key, recent_searches, 86400)
    
    @staticmethod
    def get_trending_searches(limit=5):
        """Récupère les recherches tendances"""
        # Implémentation basique - peut être améliorée avec des analytics
        return [
            {'query': 'Propriété', 'count': 15},
            {'query': 'Paiement', 'count': 12},
            {'query': 'Contrat', 'count': 8},
            {'query': 'Bailleur', 'count': 6},
            {'query': 'Locataire', 'count': 4}
        ]

