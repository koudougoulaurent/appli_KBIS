"""
Vues pour l'intégration de la validation intelligente des paiements
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from paiements.services_validation_paiements import ServiceValidationPaiements
from paiements.models import Paiement
from contrats.models import Contrat


@login_required
@require_http_methods(["POST"])
def valider_paiement_ajax(request):
    """
    Validation AJAX d'un paiement avant soumission
    """
    try:
        data = json.loads(request.body)
        contrat_id = data.get('contrat_id')
        montant = data.get('montant')
        date_paiement_str = data.get('date_paiement')
        type_paiement = data.get('type_paiement', 'loyer')
        
        if not all([contrat_id, montant, date_paiement_str]):
            return JsonResponse({
                'success': False,
                'error': 'Données manquantes'
            })
        
        # Récupérer le contrat
        try:
            contrat = Contrat.objects.get(id=contrat_id)
        except Contrat.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Contrat non trouvé'
            })
        
        # Parser la date
        try:
            date_paiement = datetime.strptime(date_paiement_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Format de date invalide'
            })
        
        # Valider le paiement
        validation = ServiceValidationPaiements.valider_paiement_intelligent(
            contrat=contrat,
            montant=float(montant),
            date_paiement=date_paiement,
            type_paiement=type_paiement
        )
        
        return JsonResponse({
            'success': True,
            'validation': validation
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la validation: {str(e)}'
        })


@login_required
def statut_paiements_contrat(request, contrat_id):
    """
    Affiche le statut complet des paiements pour un contrat
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé')
        return redirect('contrats:liste')
    
    # Obtenir le statut des paiements
    statut = ServiceValidationPaiements.obtenir_statut_paiements_contrat(contrat)
    
    context = {
        'contrat': contrat,
        'statut': statut,
        'page_title': f'Statut des paiements - {contrat}'
    }
    
    return render(request, 'paiements/statut_paiements_contrat.html', context)


@login_required
def suggerer_mois_paiement(request, contrat_id):
    """
    Suggère le prochain mois à payer pour un contrat
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Contrat non trouvé'
        })
    
    # Déterminer le mois suggéré
    mois_suggere = ServiceValidationPaiements._determiner_mois_suggere(
        contrat, timezone.now().date()
    )
    
    return JsonResponse({
        'success': True,
        'mois_suggere': mois_suggere.strftime('%Y-%m-%d') if mois_suggere else None,
        'mois_suggere_display': mois_suggere.strftime('%B %Y') if mois_suggere else None
    })


@login_required
def verifier_doublons_mois(request, contrat_id):
    """
    Vérifie s'il y a des doublons pour un mois donné
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id)
        mois_str = request.GET.get('mois')  # Format: YYYY-MM
        
        if not mois_str:
            return JsonResponse({
                'success': False,
                'error': 'Mois non spécifié'
            })
        
        # Parser le mois
        mois = datetime.strptime(mois_str, '%Y-%m').date().replace(day=1)
        
        # Analyser les paiements
        analyse = ServiceValidationPaiements._analyser_paiements_existants(contrat)
        
        # Vérifier les doublons
        doublons = analyse['paiements_par_mois'].get(mois, [])
        
        return JsonResponse({
            'success': True,
            'mois': mois_str,
            'doublons_detectes': len(doublons) > 0,
            'nombre_paiements': len(doublons),
            'paiements': [
                {
                    'id': p.id,
                    'montant': str(p.montant),
                    'date': p.date_paiement.strftime('%Y-%m-%d'),
                    'statut': p.statut
                } for p in doublons
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        })


@login_required
def historique_validation_paiements(request, contrat_id):
    """
    Affiche l'historique des validations pour un contrat
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé')
        return redirect('contrats:liste')
    
    # Récupérer tous les paiements avec leurs validations
    paiements = Paiement.objects.filter(
        contrat=contrat
    ).order_by('-date_paiement')
    
    # Analyser chaque paiement
    paiements_analyse = []
    for paiement in paiements:
        validation = ServiceValidationPaiements.valider_paiement_intelligent(
            contrat=contrat,
            montant=float(paiement.montant),
            date_paiement=paiement.date_paiement,
            type_paiement=paiement.type_paiement
        )
        
        paiements_analyse.append({
            'paiement': paiement,
            'validation': validation
        })
    
    context = {
        'contrat': contrat,
        'paiements_analyse': paiements_analyse,
        'page_title': f'Historique des validations - {contrat}'
    }
    
    return render(request, 'paiements/historique_validation_paiements.html', context)
