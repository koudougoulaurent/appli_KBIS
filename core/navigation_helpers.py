"""
Aides de navigation contextuelle pour l'application
Gestion des breadcrumbs, actions rapides et menus contextuels
"""

from typing import List, Dict, Any, Optional
from django.urls import reverse
from django.contrib.auth.models import AbstractUser


class NavigationHelper:
    """Classe utilitaire pour la gestion de la navigation contextuelle"""
    
    @staticmethod
    def create_breadcrumbs(*items: tuple) -> List[Dict[str, str]]:
        """
        Crée une liste de breadcrumbs
        
        Args:
            *items: Tuples de (label, url, icon) ou (label, None, icon)
        
        Returns:
            Liste de dictionnaires de breadcrumbs
        """
        breadcrumbs = []
        for item in items:
            if len(item) == 3:
                label, url, icon = item
            elif len(item) == 2:
                label, url = item
                icon = 'chevron-right'
            else:
                label = item[0]
                url = None
                icon = 'chevron-right'
            
            breadcrumbs.append({
                'label': label,
                'url': url,
                'icon': icon
            })
        
        return breadcrumbs
    
    @staticmethod
    def create_quick_actions(*actions: tuple) -> List[Dict[str, Any]]:
        """
        Crée une liste d'actions rapides
        
        Args:
            *actions: Tuples de (label, url, style, icon, tooltip, confirm)
        
        Returns:
            Liste de dictionnaires d'actions
        """
        quick_actions = []
        for action in actions:
            if len(action) == 6:
                label, url, style, icon, tooltip, confirm = action
            elif len(action) == 5:
                label, url, style, icon, tooltip = action
                confirm = None
            elif len(action) == 4:
                label, url, style, icon = action
                tooltip = None
                confirm = None
            elif len(action) == 3:
                label, url, style = action
                icon = 'arrow-right'
                tooltip = None
                confirm = None
            else:
                label, url = action
                style = 'btn-outline-primary'
                icon = 'arrow-right'
                tooltip = None
                confirm = None
            
            quick_actions.append({
                'label': label,
                'url': url,
                'style': style,
                'icon': icon,
                'tooltip': tooltip,
                'confirm': confirm
            })
        
        return quick_actions
    
    @staticmethod
    def create_context_menu(*sections: tuple) -> List[Dict[str, Any]]:
        """
        Crée un menu contextuel structuré
        
        Args:
            *sections: Tuples de (title, icon, actions) ou (actions,)
        
        Returns:
            Liste de sections du menu contextuel
        """
        context_menu = []
        for section in sections:
            if len(section) == 3:
                title, icon, actions = section
                context_menu.append({
                    'title': title,
                    'icon': icon,
                    'actions': NavigationHelper._parse_actions(actions)
                })
            else:
                actions = section[0]
                context_menu.append({
                    'actions': NavigationHelper._parse_actions(actions)
                })
        
        return context_menu
    
    @staticmethod
    def _parse_actions(actions: tuple) -> List[Dict[str, Any]]:
        """Parse les actions d'une section"""
        parsed_actions = []
        for action in actions:
            if len(action) == 6:
                label, url, style, icon, tooltip, confirm = action
            elif len(action) == 5:
                label, url, style, icon, tooltip = action
                confirm = None
            elif len(action) == 4:
                label, url, style, icon = action
                tooltip = None
                confirm = None
            elif len(action) == 3:
                label, url, style = action
                icon = 'arrow-right'
                tooltip = None
                confirm = None
            else:
                label, url = action
                style = 'btn-outline-secondary'
                icon = 'arrow-right'
                tooltip = None
                confirm = None
            
            parsed_actions.append({
                'label': label,
                'url': url,
                'style': style,
                'icon': icon,
                'tooltip': tooltip,
                'confirm': confirm
            })
        
        return parsed_actions


class ContractNavigationHelper(NavigationHelper):
    """Helper spécifique pour la navigation des contrats"""
    
    @staticmethod
    def get_contract_breadcrumbs(contrat) -> List[Dict[str, str]]:
        """Crée les breadcrumbs pour un contrat"""
        return NavigationHelper.create_breadcrumbs(
            ('Contrats', reverse('contrats:liste'), 'file-earmark-text'),
            (f'Contrat {contrat.numero_contrat}', None, 'file-text')
        )
    
    @staticmethod
    def get_contract_quick_actions(contrat, user: AbstractUser) -> List[Dict[str, Any]]:
        """Crée les actions rapides pour un contrat"""
        actions = [
            ('Modifier', reverse('contrats:modifier', args=[contrat.pk]), 'btn-outline-warning', 'pencil', 'Modifier ce contrat'),
            ('Gestion Caution', reverse('contrats:detail_contrat_caution', args=[contrat.pk]), 'btn-outline-primary', 'shield-check', 'Gérer la caution'),
        ]
        
        if not contrat.est_resilie:
            actions.extend([
                ('Résilier', reverse('contrats:resilier', args=[contrat.pk]), 'btn-outline-danger', 'x-circle', 'Résilier ce contrat', 'Êtes-vous sûr de vouloir résilier ce contrat ?'),
                ('Créer Résiliation', reverse('contrats:creer_resiliation', args=[contrat.pk]), 'btn-outline-warning', 'file-earmark-x', 'Créer une résiliation'),
            ])
        else:
            if hasattr(contrat, 'resiliation') and contrat.resiliation:
                actions.append(
                    ('Voir Résiliation', reverse('contrats:detail_resiliation', args=[contrat.resiliation.pk]), 'btn-outline-info', 'eye', 'Voir la résiliation')
                )
        
        if user.groupe_travail.nom.upper() == 'PRIVILEGE':
            actions.append(
                ('Supprimer', reverse('contrats:supprimer_contrat', args=[contrat.pk]), 'btn-outline-danger', 'trash', 'Supprimer ce contrat', 'Voulez-vous vraiment supprimer ce contrat ?')
            )
        
        return NavigationHelper.create_quick_actions(*actions)
    
    @staticmethod
    def get_contract_context_menu(contrat, user: AbstractUser) -> List[Dict[str, Any]]:
        """Crée le menu contextuel pour un contrat"""
        sections = [
            # Actions principales
            (
                'Actions Principales',
                'lightning',
                [
                    ('Voir Propriété', reverse('proprietes:detail', args=[contrat.propriete.pk]), 'btn-outline-primary', 'house', 'Voir les détails de la propriété'),
                    ('Voir Locataire', reverse('proprietes:detail_locataire', args=[contrat.locataire.pk]), 'btn-outline-info', 'person', 'Voir les détails du locataire'),
                ]
            ),
            # Gestion financière
            (
                'Gestion Financière',
                'cash-coin',
                [
                    ('Nouveau Paiement', reverse('paiements:ajouter'), 'btn-outline-success', 'plus-circle', 'Créer un nouveau paiement'),
                    ('Historique Paiements', reverse('paiements:historique:historique_contrat', args=[contrat.pk]), 'btn-outline-secondary', 'clock-history', 'Voir l\'historique des paiements de ce contrat'),
                    ('Gérer Cautions', reverse('contrats:liste_contrats_caution'), 'btn-outline-warning', 'shield-check', 'Gérer toutes les cautions'),
                ]
            ),
            # Documents et rapports
            (
                'Documents & Rapports',
                'file-earmark-text',
                [
                    ('Imprimer Contrat', reverse('contrats:imprimer_document_contrat', args=[contrat.pk]), 'btn-outline-secondary', 'printer', 'Imprimer le document de contrat'),
                    ('Imprimer Reçu', reverse('contrats:imprimer_recu_caution', args=[contrat.pk]), 'btn-outline-secondary', 'receipt', 'Imprimer le reçu de caution'),
                ]
            )
        ]
        
        return NavigationHelper.create_context_menu(*sections)


class PropertyNavigationHelper(NavigationHelper):
    """Helper spécifique pour la navigation des propriétés"""
    
    @staticmethod
    def get_property_breadcrumbs(propriete) -> List[Dict[str, str]]:
        """Crée les breadcrumbs pour une propriété"""
        return NavigationHelper.create_breadcrumbs(
            ('Propriétés', reverse('proprietes:liste'), 'house'),
            (propriete.titre, None, 'house-fill')
        )
    
    @staticmethod
    def get_property_quick_actions(propriete, user: AbstractUser) -> List[Dict[str, Any]]:
        """Crée les actions rapides pour une propriété"""
        actions = [
            ('Modifier', reverse('proprietes:modifier', args=[propriete.pk]), 'btn-outline-warning', 'pencil', 'Modifier cette propriété'),
            ('Nouveau Contrat', reverse('contrats:ajouter'), 'btn-outline-success', 'plus-circle', 'Créer un nouveau contrat'),
            ('Voir Bailleur', reverse('proprietes:detail_bailleur', args=[propriete.bailleur.pk]), 'btn-outline-info', 'person-badge', 'Voir les détails du bailleur'),
        ]
        
        if user.groupe_travail.nom.upper() in ['PRIVILEGE', 'ADMINISTRATION']:
            actions.append(
                ('Supprimer', reverse('proprietes:supprimer', args=[propriete.pk]), 'btn-outline-danger', 'trash', 'Supprimer cette propriété', 'Voulez-vous vraiment supprimer cette propriété ?')
            )
        
        return NavigationHelper.create_quick_actions(*actions)


class PaymentNavigationHelper(NavigationHelper):
    """Helper spécifique pour la navigation des paiements"""
    
    @staticmethod
    def get_payment_breadcrumbs(paiement) -> List[Dict[str, str]]:
        """Crée les breadcrumbs pour un paiement"""
        return NavigationHelper.create_breadcrumbs(
            ('Paiements', reverse('paiements:liste'), 'cash-coin'),
            (f'Paiement {paiement.numero_paiement}', None, 'cash')
        )
    
    @staticmethod
    def get_payment_quick_actions(paiement, user: AbstractUser) -> List[Dict[str, Any]]:
        """Crée les actions rapides pour un paiement"""
        actions = [
            ('Modifier', reverse('paiements:modifier', args=[paiement.pk]), 'btn-outline-warning', 'pencil', 'Modifier ce paiement'),
            ('Voir Contrat', reverse('contrats:detail', args=[paiement.contrat.pk]), 'btn-outline-primary', 'file-text', 'Voir le contrat associé'),
            ('Voir Propriété', reverse('proprietes:detail', args=[paiement.contrat.propriete.pk]), 'btn-outline-info', 'house', 'Voir la propriété'),
        ]
        
        if user.groupe_travail.nom.upper() in ['PRIVILEGE', 'ADMINISTRATION']:
            actions.append(
                ('Supprimer', reverse('paiements:supprimer', args=[paiement.pk]), 'btn-outline-danger', 'trash', 'Supprimer ce paiement', 'Voulez-vous vraiment supprimer ce paiement ?')
            )
        
        return NavigationHelper.create_quick_actions(*actions)
