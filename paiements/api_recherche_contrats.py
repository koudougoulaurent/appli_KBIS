"""
API de Recherche de Contrats
Endpoint pour le widget de recherche de contrats
"""
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from contrats.models import Contrat


def api_recherche_contrats(request):
    """
    API pour rechercher des contrats
    GET /paiements/api/recherche-contrats/?q=terme_recherche
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'La recherche doit contenir au moins 2 caractères'
        })
    
    try:
        # Recherche dans plusieurs champs
        contrats = Contrat.objects.filter(
            Q(est_actif=True) &
            Q(est_resilie=False) &
            Q(is_deleted=False) &
            (
                Q(numero_contrat__icontains=query) |
                Q(locataire__nom__icontains=query) |
                Q(locataire__prenom__icontains=query) |
                Q(propriete__titre__icontains=query) |
                Q(propriete__adresse__icontains=query) |
                Q(propriete__ville__icontains=query) |
                Q(loyer_mensuel__icontains=query)
            )
        ).select_related('locataire', 'propriete', 'propriete__bailleur')[:20]  # Limiter à 20 résultats
        
        # Formatter les résultats
        resultats = []
        for contrat in contrats:
            locataire_nom = f"{contrat.locataire.nom} {contrat.locataire.prenom}" if contrat.locataire else "Sans locataire"
            propriete_nom = contrat.propriete.titre if contrat.propriete else "Sans propriété"
            
            resultats.append({
                'id': contrat.id,
                'numero': contrat.numero_contrat,
                'locataire': locataire_nom,
                'propriete': propriete_nom,
                'loyer_mensuel': float(contrat.loyer_mensuel),
                'bailleur': contrat.propriete.bailleur.nom if (contrat.propriete and contrat.propriete.bailleur) else None
            })
        
        return JsonResponse({
            'success': True,
            'contrats': resultats,
            'count': len(resultats)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
