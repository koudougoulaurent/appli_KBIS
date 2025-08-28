from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json

from .services_intelligents_retraits import ServiceContexteIntelligentRetraits
from .models import RetraitBailleur
from proprietes.models import Bailleur


@method_decorator(csrf_exempt, name='dispatch')
class APIContexteIntelligentRetraits(View):
    """
    API intelligente pour récupérer automatiquement le contexte complet d'un bailleur.
    """
    
    def get(self, request, bailleur_id=None):
        """
        GET /api/contexte-intelligent-retraits/bailleur/{bailleur_id}/
        Récupère TOUTES les informations contextuelles d'un bailleur.
        """
        if not bailleur_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du bailleur requis'
            }, status=400)
        
        try:
            bailleur_id = int(bailleur_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'ID du bailleur invalide'
            }, status=400)
        
        # Récupération du contexte complet
        contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur_id)
        
        if contexte['success']:
            return JsonResponse(contexte)
        else:
            return JsonResponse(contexte, status=404)
    
    def post(self, request, bailleur_id=None):
        """
        POST /api/contexte-intelligent-retraits/bailleur/{bailleur_id}/
        Met à jour le contexte ou applique des suggestions.
        """
        if not bailleur_id:
            return JsonResponse({
                'success': False,
                'error': 'ID du bailleur requis'
            }, status=400)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'appliquer_suggestion':
                return self._appliquer_suggestion(bailleur_id, data)
            elif action == 'calculer_montants':
                return self._calculer_montants(bailleur_id, data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Action non reconnue'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données JSON invalides'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            }, status=500)
    
    def _appliquer_suggestion(self, bailleur_id, data):
        """Applique une suggestion de retrait."""
        try:
            suggestion_type = data.get('type')
            mois_retrait = data.get('mois_retrait')
            
            if not suggestion_type or not mois_retrait:
                return JsonResponse({
                    'success': False,
                    'error': 'Type de suggestion et mois requis'
                }, status=400)
            
            # Récupérer le contexte pour obtenir les montants
            contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur_id)
            
            if not contexte['success']:
                return JsonResponse(contexte, status=404)
            
            calculs = contexte['data']['calculs_automatiques']
            
            # Créer les données du retrait selon la suggestion
            if suggestion_type == 'retrait_mensuel':
                retrait_data = {
                    'bailleur_id': bailleur_id,
                    'mois_retrait': mois_retrait,
                    'montant_loyers_bruts': calculs['loyers_ce_mois'],
                    'montant_charges_deductibles': calculs['total_charges'],
                    'montant_net_a_payer': calculs['montant_net_a_payer'],
                    'type_retrait': 'mensuel',
                    'statut': 'en_attente'
                }
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Type de suggestion non supporté'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': 'Suggestion appliquée avec succès',
                'retrait_data': retrait_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de l\'application de la suggestion: {str(e)}'
            }, status=500)
    
    def _calculer_montants(self, bailleur_id, data):
        """Calcule les montants pour un retrait."""
        try:
            mois_retrait = data.get('mois_retrait')
            
            if not mois_retrait:
                return JsonResponse({
                    'success': False,
                    'error': 'Mois de retrait requis'
                }, status=400)
            
            # Récupérer le contexte pour obtenir les montants
            contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur_id)
            
            if not contexte['success']:
                return JsonResponse(contexte, status=404)
            
            calculs = contexte['data']['calculs_automatiques']
            
            return JsonResponse({
                'success': True,
                'calculs': calculs
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors du calcul des montants: {str(e)}'
            }, status=500)


@login_required
@require_http_methods(["GET"])
def api_suggestions_retrait(request, bailleur_id):
    """
    API pour récupérer les suggestions de retrait d'un bailleur.
    GET /api/suggestions-retrait/bailleur/{bailleur_id}/
    """
    try:
        bailleur_id = int(bailleur_id)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'ID du bailleur invalide'
        }, status=400)
    
    suggestions = ServiceContexteIntelligentRetraits.get_suggestions_retrait(bailleur_id)
    
    if suggestions['success']:
        return JsonResponse(suggestions)
    else:
        return JsonResponse(suggestions, status=404)


@login_required
@require_http_methods(["GET"])
def api_contexte_rapide_retrait(request, bailleur_id):
    """
    API pour récupérer rapidement le contexte essentiel d'un bailleur.
    GET /api/contexte-rapide-retrait/bailleur/{bailleur_id}/
    """
    try:
        bailleur_id = int(bailleur_id)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'ID du bailleur invalide'
        }, status=400)
    
    try:
        bailleur = Bailleur.objects.get(id=bailleur_id)
        
        # Informations essentielles seulement
        contexte_rapide = {
            'bailleur': {
                'id': bailleur.id,
                'nom': bailleur.nom,
                'prenom': bailleur.prenom,
                'code_bailleur': bailleur.code_bailleur
            },
            'calculs_rapides': ServiceContexteIntelligentRetraits._get_calculs_automatiques(bailleur),
            'alertes_rapides': ServiceContexteIntelligentRetraits._get_alertes(bailleur)[:3]  # 3 premières alertes
        }
        
        return JsonResponse({
            'success': True,
            'data': contexte_rapide
        })
        
    except Bailleur.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Bailleur non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_historique_retraits(request, bailleur_id):
    """
    API pour récupérer l'historique des retraits d'un bailleur.
    GET /api/historique-retraits/bailleur/{bailleur_id}/
    """
    try:
        bailleur_id = int(bailleur_id)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'ID du bailleur invalide'
        }, status=400)
    
    try:
        bailleur = Bailleur.objects.get(id=bailleur_id)
        historique = ServiceContexteIntelligentRetraits._get_retraits_recents(bailleur)
        
        return JsonResponse({
            'success': True,
            'data': historique
        })
        
    except Bailleur.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Bailleur non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_alertes_retrait(request, bailleur_id):
    """
    API pour récupérer les alertes d'un bailleur.
    GET /api/alertes-retrait/bailleur/{bailleur_id}/
    """
    try:
        bailleur_id = int(bailleur_id)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'ID du bailleur invalide'
        }, status=400)
    
    try:
        bailleur = Bailleur.objects.get(id=bailleur_id)
        alertes = ServiceContexteIntelligentRetraits._get_alertes(bailleur)
        
        return JsonResponse({
            'success': True,
            'data': alertes
        })
        
    except Bailleur.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Bailleur non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)

