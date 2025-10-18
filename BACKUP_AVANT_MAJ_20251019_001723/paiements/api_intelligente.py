from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json

from .services_intelligents import ServiceContexteIntelligent
from .models import Paiement
from contrats.models import Contrat


@method_decorator(csrf_exempt, name='dispatch')
class APIContexteIntelligent(View):
    """
    API intelligente pour récupérer automatiquement le contexte complet d'un contrat.
    """
    
    def get(self, request, contrat_id=None):
        """
        GET /api/contexte-intelligent/contrat/{contrat_id}/
        Récupère TOUTES les informations contextuelles d'un contrat.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        # Récupération du contexte complet
        contexte = ServiceContexteIntelligent.get_contexte_complet_contrat(contrat_id)
        
        if contexte['success']:
            return JsonResponse(contexte)
        else:
            return JsonResponse(contexte, status=404)
    
    def post(self, request, contrat_id=None):
        """
        POST /api/contexte-intelligent/contrat/{contrat_id}/
        Génère des suggestions intelligentes pour le paiement.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        # Génération des suggestions
        suggestions = ServiceContexteIntelligent.get_suggestions_paiement(contrat_id)
        
        if suggestions['success']:
            return JsonResponse(suggestions)
        else:
            return JsonResponse(suggestions, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class APISuggestionsPaiement(View):
    """
    API pour les suggestions intelligentes de paiement.
    """
    
    def get(self, request, contrat_id=None):
        """
        GET /api/suggestions-paiement/contrat/{contrat_id}/
        Récupère les suggestions de paiement pour un contrat.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        # Génération des suggestions
        suggestions = ServiceContexteIntelligent.get_suggestions_paiement(contrat_id)
        
        if suggestions['success']:
            return JsonResponse(suggestions)
        else:
            return JsonResponse(suggestions, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class APIContexteRapide(View):
    """
    API pour un contexte rapide (informations essentielles uniquement).
    """
    
    def get(self, request, contrat_id=None):
        """
        GET /api/contexte-rapide/contrat/{contrat_id}/
        Récupère les informations essentielles d'un contrat.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        try:
            contrat = Contrat.objects.select_related(
                'propriete', 'locataire'
            ).get(id=contrat_id)
            
            contexte_rapide = {
                'success': True,
                'data': {
                    'contrat': {
                        'numero': contrat.numero_contrat,
                        'loyer_mensuel': contrat.loyer_mensuel,
                        'charges_mensuelles': contrat.charges_mensuelles,
                        'jour_paiement': contrat.jour_paiement,
                    },
                    'propriete': {
                        'titre': contrat.propriete.titre,
                        'adresse': contrat.propriete.adresse,
                        'ville': contrat.propriete.ville,
                    },
                    'locataire': {
                        'nom': contrat.locataire.nom,
                        'prenom': contrat.locataire.prenom,
                        'telephone': contrat.locataire.telephone,
                    }
                }
            }
            
            return JsonResponse(contexte_rapide)
            
        except Contrat.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Contrat non trouvé'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class APICalculsAutomatiques(View):
    """
    API pour les calculs automatiques d'un contrat.
    """
    
    def get(self, request, contrat_id=None):
        """
        GET /api/calculs-automatiques/contrat/{contrat_id}/
        Récupère tous les calculs automatiques pour un contrat.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        try:
            contrat = Contrat.objects.get(id=contrat_id)
            calculs = ServiceContexteIntelligent._get_calculs_automatiques(contrat)
            
            return JsonResponse({
                'success': True,
                'data': calculs
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Contrat non trouvé'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class APIHistoriquePaiements(View):
    """
    API pour l'historique des paiements d'un contrat.
    """
    
    def get(self, request, contrat_id=None):
        """
        GET /api/historique-paiements/contrat/{contrat_id}/
        Récupère l'historique des paiements des 5 derniers mois.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        try:
            contrat = Contrat.objects.get(id=contrat_id)
            historique = ServiceContexteIntelligent._get_historique_paiements(contrat)
            
            return JsonResponse({
                'success': True,
                'data': historique
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Contrat non trouvé'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class APIAlertes(View):
    """
    API pour les alertes automatiques d'un contrat.
    """
    
    def get(self, request, contrat_id=None):
        """
        GET /api/alertes/contrat/{contrat_id}/
        Récupère toutes les alertes pour un contrat.
        """
        if not contrat_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat requis'
            }, status=400)
        
        try:
            contrat_id = int(contrat_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du contrat invalide'
            }, status=400)
        
        try:
            contrat = Contrat.objects.get(id=contrat_id)
            alertes = ServiceContexteIntelligent._get_alertes(contrat)
            
            return JsonResponse({
                'success': True,
                'data': alertes
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Contrat non trouvé'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            }, status=500)
