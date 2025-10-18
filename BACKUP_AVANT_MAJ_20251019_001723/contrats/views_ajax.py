"""
Vues AJAX pour les contrats
Fonctionnalités dynamiques et interactives
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from proprietes.models import Propriete, Locataire
from contrats.models import Contrat
import json

@login_required
@require_http_methods(["GET"])
def get_propriete_details(request, propriete_id):  # pylint: disable=unused-argument
    """
    API pour récupérer les détails d'une propriété (loyer, unités, etc.)
    """
    try:
        propriete = get_object_or_404(Propriete, pk=propriete_id)
        
        # Récupérer les unités locatives disponibles
        unites = propriete.unites_locatives.filter(statut='disponible')
        unites_data = [
            {
                'id': unite.id,
                'nom': unite.nom,
                'loyer_mensuel': float(unite.loyer_mensuel) if unite.loyer_mensuel else 0.0,
                'statut': unite.statut
            }
            for unite in unites
        ]
        
        # Récupérer les pièces disponibles
        pieces = propriete.pieces.filter(statut='disponible')
        pieces_data = [
            {
                'id': piece.id,
                'nom': piece.nom,
                'statut': piece.statut
            }
            for piece in pieces
        ]
        
        # Vérifier si la propriété a des contrats actifs
        contrats_actifs = Contrat.objects.filter(
            propriete=propriete,
            statut='actif',
            is_deleted=False
        ).count()
        
        response_data = {
            'success': True,
            'propriete': {
                'id': propriete.id,
                'titre': propriete.titre,
                'adresse': propriete.adresse,
                'ville': propriete.ville,
                'loyer_actuel': float(propriete.loyer_actuel) if propriete.loyer_actuel else 0.0,
                'type_propriete': propriete.type_propriete,
                'disponible': propriete.disponible,
                'contrats_actifs': contrats_actifs,
                'unites': unites_data,
                'pieces': pieces_data
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_locataire_details(request, locataire_id):  # pylint: disable=unused-argument
    """
    API pour récupérer les détails d'un locataire
    """
    try:
        locataire = get_object_or_404(Locataire, pk=locataire_id)
        
        # Récupérer les contrats actifs du locataire
        contrats_actifs = Contrat.objects.filter(
            locataire=locataire,
            statut='actif',
            is_deleted=False
        )
        
        contrats_data = [
            {
                'id': contrat.id,
                'numero_contrat': contrat.numero_contrat,
                'propriete': contrat.propriete.titre,
                'date_debut': contrat.date_debut.isoformat() if contrat.date_debut else None,
                'date_fin': contrat.date_fin.isoformat() if contrat.date_fin else None,
                'loyer_mensuel': float(contrat.loyer_mensuel) if contrat.loyer_mensuel else 0.0
            }
            for contrat in contrats_actifs
        ]
        
        response_data = {
            'success': True,
            'locataire': {
                'id': locataire.id,
                'nom': locataire.nom,
                'prenom': locataire.prenom,
                'email': locataire.email,
                'telephone': locataire.telephone,
                'contrats_actifs': contrats_data
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def calculate_contract_duration(request):
    """
    API pour calculer la durée du contrat et les dates importantes
    """
    try:
        data = json.loads(request.body)
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if not date_debut:
            return JsonResponse({
                'success': False,
                'error': 'Date de début requise'
            }, status=400)
        
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
        
        if date_fin:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            duree_jours = (date_fin_obj - date_debut_obj).days
            duree_mois = relativedelta(date_fin_obj, date_debut_obj).months
            duree_annees = relativedelta(date_fin_obj, date_debut_obj).years
        else:
            # Calculer automatiquement la date de fin (1 an par défaut)
            date_fin_obj = date_debut_obj + relativedelta(years=1)
            duree_jours = 365
            duree_mois = 12
            duree_annees = 1
        
        # Calculer les dates importantes
        date_preavis = date_fin_obj - timedelta(days=30)  # Préavis 1 mois
        date_renouvellement = date_fin_obj - timedelta(days=60)  # Renouvellement 2 mois avant
        
        response_data = {
            'success': True,
            'calculations': {
                'date_fin_auto': date_fin_obj.isoformat(),
                'duree_jours': duree_jours,
                'duree_mois': duree_mois,
                'duree_annees': duree_annees,
                'date_preavis': date_preavis.isoformat(),
                'date_renouvellement': date_renouvellement.isoformat()
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_available_properties(request):  # pylint: disable=unused-argument
    """
    API pour récupérer les propriétés disponibles avec leurs détails
    """
    try:
        proprietes = Propriete.objects.filter(
            disponible=True,
            is_deleted=False
        ).select_related('bailleur')
        
        proprietes_data = []
        for propriete in proprietes:
            # Vérifier s'il y a des contrats actifs
            contrats_actifs = Contrat.objects.filter(
                propriete=propriete,
                statut='actif',
                is_deleted=False
            ).count()
            
            proprietes_data.append({
                'id': propriete.id,
                'titre': propriete.titre,
                'adresse': propriete.adresse,
                'ville': propriete.ville,
                'loyer_actuel': float(propriete.loyer_actuel) if propriete.loyer_actuel else 0.0,
                'type_propriete': propriete.type_propriete,
                'bailleur': propriete.bailleur.get_nom_complet() if propriete.bailleur else 'Non défini',
                'contrats_actifs': contrats_actifs,
                'disponible': propriete.disponible
            })
        
        return JsonResponse({
            'success': True,
            'proprietes': proprietes_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
