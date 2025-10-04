"""
Générateur d'actions rapides universel pour tous les modules
Système dynamique et contextuel
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings

User = get_user_model()

class QuickActionsGenerator:
    """Générateur d'actions rapides universel"""
    
    @staticmethod
    def get_actions_for_bailleur(bailleur, request):
        """Actions rapides pour un bailleur (avec cache)"""
        cache_key = f"quick_actions_bailleur_{bailleur.pk}_{request.user.pk}"
        cached_actions = cache.get(cache_key)
        
        if cached_actions is not None:
            return cached_actions
            
        actions = [
            {
                'url': reverse('proprietes:modifier_bailleur', args=[bailleur.pk]),
                'label': 'Modifier',
                'icon': 'pencil',
                'style': 'btn-primary',
                'module': 'bailleur',
                'tooltip': f'Modifier les informations de {bailleur.get_nom_complet()}',
                'shortcut': 'Ctrl+M'
            },
            {
                'url': reverse('proprietes:ajouter'),
                'label': 'Ajouter Propriété',
                'icon': 'plus-circle',
                'style': 'btn-success',
                'module': 'propriete',
                'tooltip': 'Créer une nouvelle propriété',
                'shortcut': 'Ctrl+A'
            },
            {
                'url': reverse('proprietes:proprietes_bailleur', args=[bailleur.pk]),
                'label': 'Ses Propriétés',
                'icon': 'house',
                'style': 'btn-outline-primary',
                'module': 'propriete',
                'tooltip': f'Voir toutes les propriétés de {bailleur.get_nom_complet()}',
                'badge': bailleur.proprietes.count()
            },
            {
                'url': reverse('paiements:retraits_liste'),
                'label': 'Voir Retraits',
                'icon': 'cash-coin',
                'style': 'btn-info',
                'module': 'retrait',
                'tooltip': f'Consulter les retraits de {bailleur.get_nom_complet()}',
                'shortcut': 'Ctrl+P',
                'badge': bailleur.retraits_bailleur.count() if hasattr(bailleur, 'retraits_bailleur') else 0
            },
            {
                'url': reverse('contrats:ajouter') + f'?bailleur={bailleur.pk}',
                'label': 'Nouveau Contrat',
                'icon': 'file-contract',
                'style': 'btn-outline-success',
                'module': 'contrat',
                'tooltip': f'Créer un contrat pour {bailleur.get_nom_complet()}'
            },
            {
                'url': reverse('proprietes:ajouter_charge_bailleur') + f'?bailleur={bailleur.pk}',
                'label': 'Nouvelle Charge',
                'icon': 'receipt',
                'style': 'btn-outline-warning',
                'module': 'charge',
                'tooltip': f'Ajouter une charge pour {bailleur.get_nom_complet()}'
            }
        ]
        
        # Mettre en cache pour 5 minutes
        cache.set(cache_key, actions, 300)
        return actions
    
    @staticmethod
    def get_actions_for_locataire(locataire, request):
        """Actions rapides pour un locataire"""
        return [
            {
                'url': reverse('proprietes:modifier_locataire', args=[locataire.pk]),
                'label': 'Modifier',
                'icon': 'pencil',
                'style': 'btn-primary',
                'module': 'locataire',
                'tooltip': f'Modifier les informations de {locataire.get_nom_complet()}',
                'shortcut': 'Ctrl+M'
            },
            {
                'url': reverse('contrats:ajouter') + f'?locataire={locataire.pk}',
                'label': 'Nouveau Contrat',
                'icon': 'file-contract',
                'style': 'btn-success',
                'module': 'contrat',
                'tooltip': f'Créer un contrat pour {locataire.get_nom_complet()}',
                'shortcut': 'Ctrl+A'
            },
            {
                'url': reverse('paiements:ajouter') + f'?locataire={locataire.pk}',
                'label': 'Nouveau Paiement',
                'icon': 'cash-coin',
                'style': 'btn-info',
                'module': 'paiement',
                'tooltip': f'Enregistrer un paiement de {locataire.get_nom_complet()}',
                'shortcut': 'Ctrl+P'
            },
            {
                'url': reverse('paiements:paiements_locataire', args=[locataire.pk]),
                'label': 'Historique Paiements',
                'icon': 'clock-history',
                'style': 'btn-outline-info',
                'module': 'paiement',
                'tooltip': f'Voir l\'historique des paiements de {locataire.get_nom_complet()}',
                'badge': locataire.paiements.count() if hasattr(locataire, 'paiements') else 0
            },
            {
                'url': reverse('contrats:liste') + f'?locataire={locataire.pk}',
                'label': 'Ses Contrats',
                'icon': 'file-text',
                'style': 'btn-outline-primary',
                'module': 'contrat',
                'tooltip': f'Voir tous les contrats de {locataire.get_nom_complet()}',
                'badge': locataire.contrats.count() if hasattr(locataire, 'contrats') else 0
            }
        ]
    
    @staticmethod
    def get_actions_for_propriete(propriete, request):
        """Actions rapides pour une propriété"""
        return [
            {
                'url': reverse('proprietes:modifier', args=[propriete.pk]),
                'label': 'Modifier',
                'icon': 'pencil',
                'style': 'btn-primary',
                'module': 'propriete',
                'tooltip': f'Modifier les informations de {propriete.titre}',
                'shortcut': 'Ctrl+M'
            },
            {
                'url': reverse('contrats:ajouter') + f'?propriete={propriete.pk}',
                'label': 'Nouveau Contrat',
                'icon': 'file-contract',
                'style': 'btn-success',
                'module': 'contrat',
                'tooltip': f'Créer un contrat pour {propriete.titre}',
                'shortcut': 'Ctrl+A'
            },
            {
                'url': reverse('proprietes:gestion_pieces', args=[propriete.pk]),
                'label': 'Gérer Pièces',
                'icon': 'grid-3x3',
                'style': 'btn-info',
                'module': 'propriete',
                'tooltip': f'Gérer les pièces de {propriete.titre}',
                'badge': propriete.pieces.count() if hasattr(propriete, 'pieces') else 0
            },
            {
                'url': reverse('proprietes:photo_gallery', args=[propriete.pk]),
                'label': 'Galerie Photos',
                'icon': 'images',
                'style': 'btn-outline-info',
                'module': 'propriete',
                'tooltip': f'Voir les photos de {propriete.titre}',
                'badge': propriete.photos.count() if hasattr(propriete, 'photos') else 0
            },
            {
                'url': reverse('paiements:liste') + f'?propriete={propriete.pk}',
                'label': 'Paiements',
                'icon': 'cash-coin',
                'style': 'btn-outline-success',
                'module': 'paiement',
                'tooltip': f'Voir les paiements pour {propriete.titre}',
                'shortcut': 'Ctrl+P'
            },
            {
                'url': reverse('proprietes:ajouter_charge_bailleur') + f'?propriete={propriete.pk}',
                'label': 'Nouvelle Charge',
                'icon': 'receipt',
                'style': 'btn-outline-warning',
                'module': 'charge',
                'tooltip': f'Ajouter une charge pour {propriete.titre}'
            }
        ]
    
    @staticmethod
    def get_actions_for_contrat(contrat, request):
        """Actions rapides pour un contrat"""
        return [
            {
                'url': reverse('contrats:modifier', args=[contrat.pk]),
                'label': 'Modifier',
                'icon': 'pencil',
                'style': 'btn-primary',
                'module': 'contrat',
                'tooltip': f'Modifier le contrat {contrat.numero_contrat}',
                'shortcut': 'Ctrl+M'
            },
            {
                'url': reverse('paiements:ajouter') + f'?contrat={contrat.pk}',
                'label': 'Nouveau Paiement',
                'icon': 'cash-coin',
                'style': 'btn-success',
                'module': 'paiement',
                'tooltip': f'Enregistrer un paiement pour le contrat {contrat.numero_contrat}',
                'shortcut': 'Ctrl+A'
            },
            {
                'url': reverse('contrats:generer_quittance', args=[contrat.pk]),
                'label': 'Générer Quittance',
                'icon': 'file-earmark-text',
                'style': 'btn-info',
                'module': 'contrat',
                'tooltip': f'Générer une quittance pour {contrat.numero_contrat}'
            },
            {
                'url': reverse('contrats:renouveler', args=[contrat.pk]),
                'label': 'Renouveler',
                'icon': 'arrow-clockwise',
                'style': 'btn-outline-success',
                'module': 'contrat',
                'tooltip': f'Renouveler le contrat {contrat.numero_contrat}'
            },
            {
                'url': reverse('contrats:resilier', args=[contrat.pk]),
                'label': 'Résilier',
                'icon': 'x-circle',
                'style': 'btn-outline-danger',
                'module': 'contrat',
                'tooltip': f'Résilier le contrat {contrat.numero_contrat}',
                'confirm': 'Êtes-vous sûr de vouloir résilier ce contrat ?'
            }
        ]
    
    @staticmethod
    def get_actions_for_paiement(paiement, request):
        """Actions rapides pour un paiement"""
        return [
            {
                'url': reverse('paiements:detail', args=[paiement.pk]),
                'label': 'Modifier',
                'icon': 'pencil',
                'style': 'btn-primary',
                'module': 'paiement',
                'tooltip': f'Modifier le paiement {paiement.reference_paiement}',
                'shortcut': 'Ctrl+M'
            },
            {
                'url': reverse('paiements:valider_paiement', args=[paiement.pk]),
                'label': 'Valider',
                'icon': 'check-circle',
                'style': 'btn-success',
                'module': 'paiement',
                'tooltip': f'Valider le paiement {paiement.reference_paiement}',
                'confirm': 'Confirmer la validation de ce paiement ?'
            },
            {
                'url': reverse('paiements:refuser_paiement', args=[paiement.pk]),
                'label': 'Refuser',
                'icon': 'x-circle',
                'style': 'btn-danger',
                'module': 'paiement',
                'tooltip': f'Refuser le paiement {paiement.reference_paiement}',
                'confirm': 'Confirmer le refus de ce paiement ?'
            },
            {
                'url': reverse('paiements:detail', args=[paiement.pk]),
                'label': 'Générer Reçu',
                'icon': 'file-earmark-text',
                'style': 'btn-info',
                'module': 'paiement',
                'tooltip': f'Générer un reçu pour {paiement.reference_paiement}'
            },
            {
                'url': reverse('paiements:ajouter'),
                'label': 'Dupliquer',
                'icon': 'copy',
                'style': 'btn-outline-primary',
                'module': 'paiement',
                'tooltip': f'Dupliquer le paiement {paiement.reference_paiement}'
            }
        ]
    
    @staticmethod
    def get_actions_for_dashboard(request):
        """Actions rapides pour le dashboard"""
        return [
            {
                'url': reverse('proprietes:ajouter'),
                'label': 'Nouvelle Propriété',
                'icon': 'house-plus',
                'style': 'btn-primary',
                'module': 'propriete',
                'tooltip': 'Créer une nouvelle propriété',
                'shortcut': 'Ctrl+A'
            },
            {
                'url': reverse('proprietes:ajouter_bailleur'),
                'label': 'Nouveau Bailleur',
                'icon': 'person-plus',
                'style': 'btn-success',
                'module': 'bailleur',
                'tooltip': 'Ajouter un nouveau bailleur'
            },
            {
                'url': reverse('proprietes:ajouter_locataire'),
                'label': 'Nouveau Locataire',
                'icon': 'person-add',
                'style': 'btn-info',
                'module': 'locataire',
                'tooltip': 'Ajouter un nouveau locataire'
            },
            {
                'url': reverse('contrats:ajouter'),
                'label': 'Nouveau Contrat',
                'icon': 'file-contract',
                'style': 'btn-warning',
                'module': 'contrat',
                'tooltip': 'Créer un nouveau contrat'
            },
            {
                'url': reverse('paiements:ajouter'),
                'label': 'Nouveau Paiement',
                'icon': 'cash-coin',
                'style': 'btn-outline-success',
                'module': 'paiement',
                'tooltip': 'Enregistrer un nouveau paiement',
                'shortcut': 'Ctrl+P'
            }
        ]
    
    @staticmethod
    def get_actions_for_bailleur_retraits(bailleur, request):
        """Actions rapides pour la page des retraits d'un bailleur"""
        return [
            {
                'url': reverse('paiements:retrait_ajouter'),
                'label': 'Nouveau Retrait',
                'icon': 'plus-circle',
                'style': 'btn-success',
                'module': 'retrait',
                'tooltip': f'Créer un nouveau retrait pour {bailleur.get_nom_complet()}',
                'shortcut': 'Ctrl+A'
            },
            {
                'url': reverse('proprietes:detail_bailleur', args=[bailleur.pk]),
                'label': 'Retour au Bailleur',
                'icon': 'arrow-left',
                'style': 'btn-outline-primary',
                'module': 'bailleur',
                'tooltip': f'Retour aux détails de {bailleur.get_nom_complet()}'
            },
            {
                'url': reverse('paiements:retraits_liste'),
                'label': 'Exporter',
                'icon': 'download',
                'style': 'btn-outline-info',
                'module': 'retrait',
                'tooltip': f'Exporter les retraits de {bailleur.get_nom_complet()}'
            },
            {
                'url': reverse('paiements:retraits_liste'),
                'label': 'Rapport',
                'icon': 'file-earmark-text',
                'style': 'btn-outline-success',
                'module': 'retrait',
                'tooltip': f'Générer un rapport des retraits de {bailleur.get_nom_complet()}'
            }
        ]
    
    @staticmethod
    def get_actions_for_retrait_bailleur(retrait, request):
        """Actions rapides pour un retrait spécifique"""
        return [
            {
                'url': reverse('paiements:retrait_modifier', args=[retrait.pk]),
                'label': 'Modifier',
                'icon': 'pencil',
                'style': 'btn-primary',
                'module': 'retrait',
                'tooltip': f'Modifier le retrait de {retrait.mois_retrait.strftime("%B %Y")}',
                'shortcut': 'Ctrl+M'
            },
            {
                'url': reverse('paiements:valider_retrait', args=[retrait.pk]),
                'label': 'Valider',
                'icon': 'check-circle',
                'style': 'btn-success',
                'module': 'retrait',
                'tooltip': f'Valider le retrait de {retrait.mois_retrait.strftime("%B %Y")}',
                'confirm': 'Confirmer la validation de ce retrait ?'
            },
            {
                'url': reverse('paiements:marquer_retrait_paye', args=[retrait.pk]),
                'label': 'Marquer Payé',
                'icon': 'cash-coin',
                'style': 'btn-info',
                'module': 'retrait',
                'tooltip': f'Marquer le retrait de {retrait.mois_retrait.strftime("%B %Y")} comme payé'
            },
            {
                'url': reverse('paiements:generer_quittance_retrait', args=[retrait.pk]),
                'label': 'Générer Reçu',
                'icon': 'file-earmark-text',
                'style': 'btn-outline-primary',
                'module': 'retrait',
                'tooltip': f'Générer un reçu pour le retrait de {retrait.mois_retrait.strftime("%B %Y")}'
            },
            {
                'url': reverse('paiements:retraits_liste'),
                'label': 'Retour Liste',
                'icon': 'arrow-left',
                'style': 'btn-outline-secondary',
                'module': 'retrait',
                'tooltip': 'Retour à la liste des retraits'
            }
        ]
    
    @classmethod
    def get_actions_for_context(cls, context, request):
        """Génère les actions rapides selon le contexte"""
        if 'bailleur' in context:
            return cls.get_actions_for_bailleur(context['bailleur'], request)
        elif 'locataire' in context:
            return cls.get_actions_for_locataire(context['locataire'], request)
        elif 'propriete' in context:
            return cls.get_actions_for_propriete(context['propriete'], request)
        elif 'contrat' in context:
            return cls.get_actions_for_contrat(context['contrat'], request)
        elif 'paiement' in context:
            return cls.get_actions_for_paiement(context['paiement'], request)
        else:
            return cls.get_actions_for_dashboard(request)
