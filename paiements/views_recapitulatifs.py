#!/usr/bin/env python3
"""
Vues pour la gestion des récapitulatifs mensuels
================================================

Ce module gère la création, validation et envoi des récapitulatifs mensuels
qui résument toutes les opérations financières pour chaque bailleur.
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import RecapitulatifMensuelBailleur
from .forms import (
    RecapitulatifMensuelBailleurForm,
    RecapitulatifMensuelValidationForm,
    RecapitulatifMensuelEnvoiForm
)
from proprietes.models import Bailleur, Propriete

logger = logging.getLogger(__name__)


@login_required
def liste_recapitulatifs(request):
    """Liste de tous les récapitulatifs mensuels."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    # Filtres
    mois = request.GET.get('mois')
    statut = request.GET.get('statut')
    type_recap = request.GET.get('type')
    
    recapitulatifs = RecapitulatifMensuelBailleur.objects.all()
    
    # Appliquer les filtres
    if mois:
        recapitulatifs = recapitulatifs.filter(mois_recapitulatif__icontains=mois)
    if statut:
        recapitulatifs = recapitulatifs.filter(statut=statut)
    if type_recap:
        recapitulatifs = recapitulatifs.filter(type_recapitulatif=type_recap)
    
    # Pagination
    paginator = Paginator(recapitulatifs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': recapitulatifs.count(),
        'en_preparation': recapitulatifs.filter(statut='en_preparation').count(),
        'valides': recapitulatifs.filter(statut='valide').count(),
        'envoyes': recapitulatifs.filter(statut='envoye').count(),
        'payes': recapitulatifs.filter(statut='paye').count(),
    }
    
    context = {
        'page_title': 'Récapitulatifs Mensuels',
        'page_icon': 'file-earmark-text',
        'page_obj': page_obj,
        'stats': stats,
        'filtres': {
            'mois': mois,
            'statut': statut,
            'type_recap': type_recap
        }
    }
    
    return render(request, 'paiements/recapitulatifs/liste_recapitulatifs.html', context)


@login_required
def creer_recapitulatif(request):
    """Créer un nouveau récapitulatif mensuel."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    if request.method == 'POST':
        form = RecapitulatifMensuelBailleurForm(request.POST)
        if form.is_valid():
            recapitulatif = form.save(commit=False)
            recapitulatif.gestionnaire = request.user
            recapitulatif.save()
            
            messages.success(
                request,
                f"Récapitulatif {recapitulatif.get_type_recapitulatif_display()} "
                f"créé avec succès pour {recapitulatif.mois_recapitulatif.strftime('%B %Y')}"
            )
            
            return redirect('paiements:detail_recapitulatif', recapitulatif.pk)
    else:
        form = RecapitulatifMensuelBailleurForm()
    
    context = {
        'page_title': 'Créer un Récapitulatif Mensuel',
        'page_icon': 'plus-circle',
        'form': form,
        'action': 'creer'
    }
    
    return render(request, 'paiements/recapitulatifs/creer_recapitulatif.html', context)


@login_required
def detail_recapitulatif(request, recapitulatif_id):
    """Détail d'un récapitulatif mensuel."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    # Calculer les totaux
    totaux = recapitulatif.calculer_totaux_bailleur()
    
    # Formulaires d'action
    form_validation = RecapitulatifMensuelValidationForm()
    form_envoi = RecapitulatifMensuelEnvoiForm()
    
    context = {
        'page_title': f'Récapitulatif {recapitulatif.get_type_recapitulatif_display()} - {recapitulatif.mois_recapitulatif.strftime("%B %Y")}',
        'page_icon': 'file-earmark-text',
        'recapitulatif': recapitulatif,
        'totaux': totaux,
        'form_validation': form_validation,
        'form_envoi': form_envoi
    }
    
    return render(request, 'paiements/recapitulatifs/detail_recapitulatif.html', context)


@login_required
def valider_recapitulatif(request, recapitulatif_id):
    """Valider un récapitulatif mensuel."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    if not recapitulatif.peut_etre_valide():
        return JsonResponse({
            'success': False,
            'message': 'Ce récapitulatif ne peut pas être validé'
        })
    
    try:
        recapitulatif.valider(request.user)
        
        # Log de l'action
        logger.info(
            f"Récapitulatif {recapitulatif.pk} validé par {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Récapitulatif validé avec succès',
            'nouveau_statut': recapitulatif.get_statut_display(),
            'date_validation': recapitulatif.date_validation.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation du récapitulatif {recapitulatif.pk}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        })


@login_required
def envoyer_recapitulatif(request, recapitulatif_id):
    """Envoyer un récapitulatif mensuel au bailleur."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    if not recapitulatif.peut_etre_envoye():
        return JsonResponse({
            'success': False,
            'message': 'Ce récapitulatif ne peut pas être envoyé'
        })
    
    try:
        recapitulatif.envoyer_au_bailleur()
        
        # Log de l'action
        logger.info(
            f"Récapitulatif {recapitulatif.pk} envoyé par {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Récapitulatif marqué comme envoyé',
            'nouveau_statut': recapitulatif.get_statut_display(),
            'date_envoi': recapitulatif.date_envoi.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du récapitulatif {recapitulatif.pk}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de l\'envoi: {str(e)}'
        })


@login_required
def marquer_paye_recapitulatif(request, recapitulatif_id):
    """Marquer un récapitulatif mensuel comme payé."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    if not recapitulatif.peut_etre_paye():
        return JsonResponse({
            'success': False,
            'message': 'Ce récapitulatif ne peut pas être marqué comme payé'
        })
    
    try:
        recapitulatif.marquer_comme_paye()
        
        # Log de l'action
        logger.info(
            f"Récapitulatif {recapitulatif.pk} marqué comme payé par {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Récapitulatif marqué comme payé',
            'nouveau_statut': recapitulatif.get_statut_display(),
            'date_paiement': recapitulatif.date_paiement.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du marquage payé du récapitulatif {recapitulatif.pk}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du marquage: {str(e)}'
        })


@login_required
def telecharger_pdf_recapitulatif(request, recapitulatif_id):
    """Télécharger le PDF du récapitulatif mensuel."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    try:
        # Générer le PDF
        pdf_content = recapitulatif.generer_pdf_recapitulatif()
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{recapitulatif.get_nom_fichier_pdf()}"'
        
        # Log de l'action
        logger.info(
            f"PDF du récapitulatif {recapitulatif.pk} téléchargé par {request.user.username}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF du récapitulatif {recapitulatif.pk}: {e}")
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('paiements:detail_recapitulatif', recapitulatif.pk)


@login_required
def apercu_recapitulatif(request, recapitulatif_id):
    """Aperçu HTML du récapitulatif mensuel."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    totaux = recapitulatif.calculer_totaux_bailleur()
    
    context = {
        'recapitulatif': recapitulatif,
        'totaux': totaux,
        'date_generation': timezone.now(),
        'apercu': True
    }
    
    return render(request, 'paiements/recapitulatifs/apercu_recapitulatif.html', context)


@login_required
def statistiques_recapitulatifs(request):
    """Statistiques des récapitulatifs mensuels."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    # Statistiques par mois
    stats_mensuelles = RecapitulatifMensuelBailleur.objects.values('mois_recapitulatif').annotate(
        nombre=Count('id')
    ).order_by('-mois_recapitulatif')[:12]
    
    # Calculer les totaux pour chaque mois
    for stat in stats_mensuelles:
        mois = stat['mois_recapitulatif']
        recapitulatifs_mois = RecapitulatifMensuelBailleur.objects.filter(mois_recapitulatif=mois)
        
        from decimal import Decimal
        total_loyers = Decimal('0')
        total_charges = Decimal('0')
        total_net = Decimal('0')
        
        for recap in recapitulatifs_mois:
            totaux = recap.calculer_totaux_globaux()
            total_loyers += totaux['total_loyers_bruts']
            total_charges += totaux['total_charges_deductibles']
            total_net += totaux['total_net_a_payer']
        
        stat['total_loyers'] = total_loyers
        stat['total_charges'] = total_charges
        stat['total_net'] = total_net
    
    # Statistiques par statut
    stats_statut = RecapitulatifMensuelBailleur.objects.values('statut').annotate(
        nombre=Count('id')
    ).order_by('statut')
    
    # Statistiques par type
    stats_type = RecapitulatifMensuelBailleur.objects.values('type_recapitulatif').annotate(
        nombre=Count('id')
    ).order_by('type_recapitulatif')
    
    context = {
        'page_title': 'Statistiques des Récapitulatifs',
        'page_icon': 'graph-up',
        'stats_mensuelles': stats_mensuelles,
        'stats_statut': stats_statut,
        'stats_type': stats_type
    }
    
    return render(request, 'paiements/recapitulatifs/statistiques_recapitulatifs.html', context)


@login_required
def generer_recapitulatif_automatique(request):
    """Générer automatiquement le récapitulatif du mois en cours."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        messages.error(request, "Vous devez être dans le groupe PRIVILEGE pour accéder à cette page.")
        return redirect('utilisateurs:connexion_groupes')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    try:
        # Vérifier s'il existe déjà un récapitulatif pour ce mois
        mois_actuel = timezone.now().replace(day=1)
        
        if RecapitulatifMensuelBailleur.objects.filter(
            mois_recapitulatif=mois_actuel,
            type_recapitulatif='mensuel'
        ).exists():
            return JsonResponse({
                'success': False,
                'message': f'Un récapitulatif mensuel existe déjà pour {mois_actuel.strftime("%B %Y")}'
            })
        
        # Créer le récapitulatif automatiquement
        recapitulatif = RecapitulatifMensuelBailleur.objects.create(
            mois_recapitulatif=mois_actuel,
            type_recapitulatif='mensuel',
            gestionnaire=request.user,
            notes='Généré automatiquement'
        )
        
        # Log de l'action
        logger.info(
            f"Récapitulatif automatique {recapitulatif.pk} créé par {request.user.username} "
            f"pour {mois_actuel.strftime('%B %Y')}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Récapitulatif automatique créé pour {mois_actuel.strftime("%B %Y")}',
            'recapitulatif_id': recapitulatif.pk,
            'redirect_url': reverse('paiements:detail_recapitulatif', args=[recapitulatif.pk])
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération automatique du récapitulatif: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la génération: {str(e)}'
        })
