"""
Vues pour la génération de récépissés KBIS dynamiques
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from core.utils import check_group_permissions
from .models import Paiement, RetraitBailleur, RecapitulatifMensuelBailleur


@login_required
def generer_recu_kbis_dynamique(request, paiement_pk):
    """Génère un récépissé avec le nouveau système KBIS IMMOBILIER dynamique."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail', pk=paiement_pk)
    
    try:
        paiement = get_object_or_404(Paiement, pk=paiement_pk)
        
        # Génération directe avec le système KBIS dynamique
        html_recu = paiement._generer_recu_kbis_dynamique()
        
        if html_recu:
            # Retourner directement le HTML (format A5 prêt pour impression)
            return HttpResponse(html_recu, content_type='text/html')
        else:
            messages.error(request, 'Erreur lors de la génération du récépissé KBIS')
            return redirect('paiements:detail', pk=paiement_pk)
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération: {str(e)}')
        return redirect('paiements:detail', pk=paiement_pk)


@login_required
def generer_recu_retrait_kbis(request, retrait_pk):
    """Génère un récépissé de retrait avec le système KBIS dynamique."""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_bailleur')
    
    try:
        retrait = get_object_or_404(RetraitBailleur, pk=retrait_pk)
        
        # Génération du récépissé de retrait
        html_recu = retrait._generer_recu_retrait_kbis()
        
        if html_recu:
            return HttpResponse(html_recu, content_type='text/html')
        else:
            messages.error(request, 'Erreur lors de la génération du récépissé de retrait KBIS')
            return redirect('paiements:retraits_bailleur')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération: {str(e)}')
        return redirect('paiements:retraits_bailleur')


@login_required
def generer_recu_recapitulatif_kbis(request, recapitulatif_pk):
    """Génère un récépissé de récapitulatif avec le système KBIS dynamique."""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels')
    
    try:
        recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_pk)
        
        # Génération du récépissé de récapitulatif
        html_recu = recapitulatif._generer_recu_recapitulatif_kbis()
        
        if html_recu:
            return HttpResponse(html_recu, content_type='text/html')
        else:
            messages.error(request, 'Erreur lors de la génération du récépissé de récapitulatif KBIS')
            return redirect('paiements:liste_recaps_mensuels')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération: {str(e)}')
        return redirect('paiements:liste_recaps_mensuels')


@login_required
def generer_quittance_retrait_kbis(request, retrait_pk):
    """Génère une quittance de retrait avec le système KBIS dynamique."""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_bailleur')
    
    try:
        retrait = get_object_or_404(RetraitBailleur, pk=retrait_pk)
        
        # Génération de la quittance de retrait
        html_quittance = retrait._generer_quittance_retrait_kbis()
        
        if html_quittance:
            return HttpResponse(html_quittance, content_type='text/html')
        else:
            messages.error(request, 'Erreur lors de la génération de la quittance de retrait KBIS')
            return redirect('paiements:retraits_bailleur')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération: {str(e)}')
        return redirect('paiements:retraits_bailleur')
