"""
Système de navigation dynamique et contextuelle
Améliore l'expérience utilisateur avec des liens intelligents
"""

from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class DynamicNavigationSystem:
    """
    Système de navigation dynamique qui s'adapte au contexte utilisateur
    """
    
    @staticmethod
    def get_contextual_links(request, current_module=None, object_id=None):
        """
        Génère des liens contextuels basés sur le module actuel et l'objet
        """
        cache_key = f"contextual_links_{request.user.pk}_{current_module}_{object_id}"
        cached_links = cache.get(cache_key)
        
        if cached_links is not None:
            return cached_links
            
        links = {
            'primary': [],
            'secondary': [],
            'quick_actions': [],
            'breadcrumbs': []
        }
        
        # Navigation primaire basée sur le module actuel
        if current_module == 'proprietes':
            links['primary'] = DynamicNavigationSystem._get_proprietes_links(request, object_id)
        elif current_module == 'paiements':
            links['primary'] = DynamicNavigationSystem._get_paiements_links(request, object_id)
        elif current_module == 'contrats':
            links['primary'] = DynamicNavigationSystem._get_contrats_links(request, object_id)
        elif current_module == 'utilisateurs':
            links['primary'] = DynamicNavigationSystem._get_utilisateurs_links(request, object_id)
        
        # Liens secondaires intelligents
        links['secondary'] = DynamicNavigationSystem._get_secondary_links(request, current_module, object_id)
        
        # Actions rapides contextuelles
        links['quick_actions'] = DynamicNavigationSystem._get_quick_actions(request, current_module, object_id)
        
        # Breadcrumbs dynamiques
        links['breadcrumbs'] = DynamicNavigationSystem._get_breadcrumbs(request, current_module, object_id)
        
        # Cache pour 5 minutes
        cache.set(cache_key, links, 300)
        return links
    
    @staticmethod
    def _get_proprietes_links(request, object_id):
        """Liens contextuels pour le module propriétés"""
        links = [
            {
                'url': reverse('proprietes:dashboard'),
                'label': 'Dashboard Propriétés',
                'icon': 'speedometer2',
                'active': True
            },
            {
                'url': reverse('proprietes:ajouter'),
                'label': 'Nouvelle Propriété',
                'icon': 'plus-circle',
                'style': 'btn-success'
            },
            {
                'url': reverse('proprietes:liste'),
                'label': 'Toutes les Propriétés',
                'icon': 'list-ul'
            }
        ]
        
        if object_id:
            # Liens spécifiques à une propriété
            try:
                from proprietes.models import Propriete
                propriete = Propriete.objects.get(pk=object_id)
                
                links.extend([
                    {
                        'url': reverse('proprietes:detail', args=[object_id]),
                        'label': f'Détail - {propriete.numero_propriete}',
                        'icon': 'eye',
                        'active': True
                    },
                    {
                        'url': reverse('proprietes:modifier', args=[object_id]),
                        'label': 'Modifier',
                        'icon': 'pencil',
                        'style': 'btn-warning'
                    }
                ])
            except:
                pass
                
        return links
    
    @staticmethod
    def _get_paiements_links(request, object_id):
        """Liens contextuels pour le module paiements"""
        links = [
            {
                'url': reverse('paiements:dashboard'),
                'label': 'Dashboard Paiements',
                'icon': 'credit-card',
                'active': True
            },
            {
                'url': reverse('paiements:ajouter'),
                'label': 'Nouveau Paiement',
                'icon': 'plus-circle',
                'style': 'btn-success'
            },
            {
                'url': reverse('paiements:liste'),
                'label': 'Tous les Paiements',
                'icon': 'list-ul'
            }
        ]
        
        # Statistiques en temps réel
        try:
            from paiements.models import Paiement
            stats = Paiement.objects.aggregate(
                total=Count('id'),
                valides=Count('id', filter=Q(statut='valide')),
                en_attente=Count('id', filter=Q(statut='en_attente')),
                montant_total=Sum('montant')
            )
            
            if stats['en_attente'] > 0:
                links.append({
                    'url': reverse('paiements:liste') + '?statut=en_attente',
                    'label': f'Paiements en Attente ({stats["en_attente"]})',
                    'icon': 'clock',
                    'style': 'btn-warning',
                    'badge': stats['en_attente']
                })
        except:
            pass
            
        return links
    
    @staticmethod
    def _get_contrats_links(request, object_id):
        """Liens contextuels pour le module contrats"""
        links = [
            {
                'url': reverse('contrats:dashboard'),
                'label': 'Dashboard Contrats',
                'icon': 'file-text',
                'active': True
            },
            {
                'url': reverse('contrats:ajouter'),
                'label': 'Nouveau Contrat',
                'icon': 'plus-circle',
                'style': 'btn-success'
            },
            {
                'url': reverse('contrats:liste'),
                'label': 'Tous les Contrats',
                'icon': 'list-ul'
            }
        ]
        
        # Contrats expirant bientôt
        try:
            from contrats.models import Contrat
            from datetime import date, timedelta
            
            date_limite = date.today() + timedelta(days=30)
            contrats_expirant = Contrat.objects.filter(
                date_fin__lte=date_limite,
                date_fin__gte=date.today(),
                statut='actif'
            ).count()
            
            if contrats_expirant > 0:
                links.append({
                    'url': reverse('contrats:liste') + '?expirant=1',
                    'label': f'Contrats Expirant ({contrats_expirant})',
                    'icon': 'exclamation-triangle',
                    'style': 'btn-warning',
                    'badge': contrats_expirant
                })
        except:
            pass
            
        return links
    
    @staticmethod
    def _get_utilisateurs_links(request, object_id):
        """Liens contextuels pour le module utilisateurs"""
        return [
            {
                'url': reverse('utilisateurs:dashboard_principal'),
                'label': 'Dashboard Utilisateurs',
                'icon': 'people',
                'active': True
            },
            {
                'url': reverse('utilisateurs:ajouter'),
                'label': 'Nouvel Utilisateur',
                'icon': 'person-plus',
                'style': 'btn-success'
            },
            {
                'url': reverse('utilisateurs:liste'),
                'label': 'Tous les Utilisateurs',
                'icon': 'list-ul'
            }
        ]
    
    @staticmethod
    def _get_secondary_links(request, current_module, object_id):
        """Liens secondaires intelligents basés sur le contexte"""
        secondary_links = []
        
        # Liens vers les modules connexes
        if current_module == 'proprietes':
            secondary_links.extend([
                {
                    'url': reverse('contrats:liste'),
                    'label': 'Contrats',
                    'icon': 'file-text',
                    'description': 'Gérer les contrats de location'
                },
                {
                    'url': reverse('paiements:liste'),
                    'label': 'Paiements',
                    'icon': 'credit-card',
                    'description': 'Gérer les paiements'
                }
            ])
        elif current_module == 'paiements':
            secondary_links.extend([
                {
                    'url': reverse('proprietes:liste'),
                    'label': 'Propriétés',
                    'icon': 'house',
                    'description': 'Gérer le portefeuille'
                },
                {
                    'url': reverse('contrats:liste'),
                    'label': 'Contrats',
                    'icon': 'file-text',
                    'description': 'Gérer les contrats'
                }
            ])
        
        return secondary_links
    
    @staticmethod
    def _get_quick_actions(request, current_module, object_id):
        """Actions rapides contextuelles"""
        quick_actions = []
        
        # Actions communes
        quick_actions.extend([
            {
                'url': reverse('core:intelligent_search'),
                'label': 'Recherche Intelligente',
                'icon': 'search',
                'style': 'btn-info',
                'shortcut': 'Ctrl+K'
            }
        ])
        
        # Actions spécifiques au module
        if current_module == 'proprietes':
            quick_actions.extend([
                {
                    'url': reverse('proprietes:ajouter'),
                    'label': 'Nouvelle Propriété',
                    'icon': 'plus-circle',
                    'style': 'btn-success',
                    'shortcut': 'Ctrl+N'
                }
            ])
        elif current_module == 'paiements':
            quick_actions.extend([
                {
                    'url': reverse('paiements:ajouter'),
                    'label': 'Nouveau Paiement',
                    'icon': 'plus-circle',
                    'style': 'btn-success',
                    'shortcut': 'Ctrl+P'
                }
            ])
        
        return quick_actions
    
    @staticmethod
    def _get_breadcrumbs(request, current_module, object_id):
        """Breadcrumbs dynamiques"""
        breadcrumbs = [
            {
                'url': reverse('core:dashboard'),
                'label': 'Dashboard',
                'icon': 'house'
            }
        ]
        
        if current_module:
            module_labels = {
                'proprietes': 'Propriétés',
                'paiements': 'Paiements',
                'contrats': 'Contrats',
                'utilisateurs': 'Utilisateurs'
            }
            
            breadcrumbs.append({
                'url': reverse(f'{current_module}:dashboard'),
                'label': module_labels.get(current_module, current_module.title()),
                'icon': 'folder'
            })
        
        return breadcrumbs

