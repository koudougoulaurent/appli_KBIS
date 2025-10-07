#!/usr/bin/env python
"""
Vues pour le monitoring des avances de loyer
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal

from .services_monitoring_avance import ServiceMonitoringAvance
from .services_avance import ServiceGestionAvance
from .models_avance import AvanceLoyer, ConsommationAvance
from contrats.models import Contrat


@login_required
def monitoring_avances(request):
    """
    Vue principale du monitoring des avances
    """
    try:
        # Générer le rapport de progression
        rapport = ServiceMonitoringAvance.generer_rapport_progression()
        
        # Détecter les avances critiques
        avances_critiques = ServiceMonitoringAvance.detecter_avances_critiques()
        
        # Récupérer les avances récentes
        avances_recentes = AvanceLoyer.objects.select_related(
            'contrat', 'contrat__locataire', 'contrat__propriete'
        ).order_by('-created_at')[:10]
        
        context = {
            'rapport': rapport,
            'avances_critiques': avances_critiques,
            'avances_recentes': avances_recentes,
            'date_actuelle': timezone.now(),
        }
        
        return render(request, 'paiements/avances/monitoring_avances.html', context)
        
    except Exception as e:
        context = {
            'erreur': f"Erreur lors du chargement du monitoring: {str(e)}",
            'date_actuelle': timezone.now(),
        }
        return render(request, 'paiements/avances/monitoring_avances.html', context)


@login_required
def detail_progression_avance(request, avance_id):
    """
    Détail de la progression d'une avance spécifique
    """
    try:
        avance = get_object_or_404(AvanceLoyer, id=avance_id)
        
        # Analyser la progression de cette avance
        progression = ServiceMonitoringAvance.analyser_progression_avance(avance)
        
        # Récupérer l'historique des consommations
        consommations = ConsommationAvance.objects.filter(avance=avance).order_by('-mois_consomme')
        
        # Récupérer l'historique des paiements du contrat
        historique_paiements = ServiceGestionAvance.get_historique_paiements_contrat(avance.contrat)
        
        # Calculer les statistiques détaillées
        stats_detaillees = {
            'montant_initial': avance.montant_avance,
            'montant_consomme': progression['montant_reel_consomme'] if progression else Decimal('0'),
            'montant_restant': avance.montant_restant,
            'pourcentage_consomme': progression['pourcentage_reel'] if progression else 0,
            'mois_ecoules': progression['mois_ecoules'] if progression else 0,
            'mois_restants_estimes': progression['mois_restants_estimes'] if progression else 0,
            'date_expiration_estimee': progression['date_expiration_estimee'] if progression else None,
            'statut_progression': progression['statut_progression'] if progression else 'inconnu'
        }
        
        context = {
            'avance': avance,
            'progression': progression,
            'consommations': consommations,
            'historique_paiements': historique_paiements[:12],  # 12 derniers mois
            'stats_detaillees': stats_detaillees,
        }
        
        return render(request, 'paiements/avances/detail_progression_avance.html', context)
        
    except Exception as e:
        context = {
            'erreur': f"Erreur lors du chargement des détails: {str(e)}",
        }
        return render(request, 'paiements/avances/detail_progression_avance.html', context)


@login_required
def synchroniser_avances_ajax(request):
    """
    Synchronise les avances via AJAX
    """
    if request.method == 'POST':
        try:
            # Synchroniser les consommations
            resultat = ServiceMonitoringAvance.synchroniser_consommations()
            
            if resultat:
                return JsonResponse({
                    'success': True,
                    'message': 'Synchronisation réussie'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Erreur lors de la synchronisation'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@login_required
def envoyer_alertes_ajax(request):
    """
    Envoie les alertes via AJAX
    """
    if request.method == 'POST':
        try:
            # Envoyer les alertes
            message = ServiceMonitoringAvance.envoyer_alertes_expiration()
            
            if message:
                return JsonResponse({
                    'success': True,
                    'message': 'Alertes envoyées',
                    'details': message
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Aucune alerte à envoyer'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@login_required
def rapport_progression_ajax(request):
    """
    Génère un rapport de progression via AJAX
    """
    if request.method == 'GET':
        try:
            # Générer le rapport
            rapport = ServiceMonitoringAvance.generer_rapport_progression()
            
            if rapport:
                return JsonResponse({
                    'success': True,
                    'rapport': rapport
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Erreur lors de la génération du rapport'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
