"""
Vues pour la validation des paiements
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from core.utils import check_group_permissions
from .models import Paiement
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
@csrf_protect
def valider_paiement(request, pk):
    """Valider un paiement en attente"""
    
    # Vérifier les permissions - seuls PRIVILEGE et COMPTABILITE peuvent valider
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, "Vous n'avez pas l'autorisation de valider les paiements.")
        return redirect('paiements:liste')
    
    # Récupérer le paiement
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérifier que le paiement est en attente
    if paiement.statut != 'en_attente':
        messages.warning(request, f"Ce paiement a déjà le statut '{paiement.get_statut_display()}'.")
        return redirect('paiements:detail', pk=pk)
    
    # Valider le paiement
    paiement.statut = 'valide'
    paiement.date_validation = timezone.now()
    paiement.valide_par = request.user
    paiement.save()
    
    # Log de l'action
    logger.info(f"Paiement {paiement.reference_paiement} validé par {request.user.username}")
    
    # Message de succès
    messages.success(
        request, 
        f"Paiement {paiement.reference_paiement} validé avec succès !"
    )
    
    return redirect('paiements:detail', pk=pk)

@login_required
@require_POST
@csrf_protect
def refuser_paiement(request, pk):
    """Refuser un paiement en attente"""
    
    # Vérifier les permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, "Vous n'avez pas l'autorisation de refuser les paiements.")
        return redirect('paiements:liste')
    
    # Récupérer le paiement
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérifier que le paiement est en attente
    if paiement.statut != 'en_attente':
        messages.warning(request, f"Ce paiement a déjà le statut '{paiement.get_statut_display()}'.")
        return redirect('paiements:detail', pk=pk)
    
    # Récupérer la raison du refus
    raison_refus = request.POST.get('raison_refus', '').strip()
    if not raison_refus:
        messages.error(request, "Veuillez indiquer la raison du refus.")
        return redirect('paiements:detail', pk=pk)
    
    # Refuser le paiement
    paiement.statut = 'refuse'
    paiement.date_refus = timezone.now()
    paiement.refuse_par = request.user
    paiement.raison_refus = raison_refus
    paiement.save()
    
    # Log de l'action
    logger.info(f"Paiement {paiement.reference_paiement} refusé par {request.user.username}: {raison_refus}")
    
    # Message de succès
    messages.warning(
        request, 
        f"Paiement {paiement.reference_paiement} refusé : {raison_refus}"
    )
    
    return redirect('paiements:detail', pk=pk)

@login_required
@require_POST
@csrf_protect
def annuler_paiement(request, pk):
    """Annuler un paiement"""
    
    # Vérifier les permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, "Vous n'avez pas l'autorisation d'annuler les paiements.")
        return redirect('paiements:liste')
    
    # Récupérer le paiement
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérifier que le paiement peut être annulé
    if paiement.statut == 'annule':
        messages.warning(request, "Ce paiement est déjà annulé.")
        return redirect('paiements:detail', pk=pk)
    
    # Récupérer la raison de l'annulation
    raison_annulation = request.POST.get('raison_annulation', '').strip()
    if not raison_annulation:
        messages.error(request, "Veuillez indiquer la raison de l'annulation.")
        return redirect('paiements:detail', pk=pk)
    
    # Annuler le paiement
    ancien_statut = paiement.get_statut_display()
    paiement.statut = 'annule'
    paiement.date_annulation = timezone.now()
    paiement.annule_par = request.user
    paiement.raison_annulation = raison_annulation
    paiement.save()
    
    # Log de l'action
    logger.info(f"Paiement {paiement.reference_paiement} annulé par {request.user.username}: {raison_annulation}")
    
    # Message de succès
    messages.info(
        request, 
        f"Paiement {paiement.reference_paiement} annulé (était {ancien_statut}) : {raison_annulation}"
    )
    
    return redirect('paiements:detail', pk=pk)

@login_required
def paiement_actions_ajax(request, pk):
    """Actions AJAX pour les paiements"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    action = request.POST.get('action')
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérifier les permissions selon l'action
    if action in ['valider', 'refuser']:
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'COMPTABILITE', 'CAISSE'], 'change')
    elif action == 'annuler':
        permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    else:
        return JsonResponse({'error': 'Action non reconnue'}, status=400)
    
    if not permissions['allowed']:
        return JsonResponse({'error': permissions['message']}, status=403)
    
    try:
        if action == 'valider':
            if paiement.statut != 'en_attente':
                return JsonResponse({'error': f'Paiement déjà {paiement.get_statut_display()}'}, status=400)
            
            paiement.statut = 'valide'
            paiement.date_validation = timezone.now()
            paiement.valide_par = request.user
            paiement.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Paiement {paiement.reference_paiement} validé avec succès',
                'new_status': 'valide',
                'new_status_display': 'Validé'
            })
            
        elif action == 'refuser':
            raison = request.POST.get('raison', '').strip()
            if not raison:
                return JsonResponse({'error': 'Raison du refus requise'}, status=400)
            
            if paiement.statut != 'en_attente':
                return JsonResponse({'error': f'Paiement déjà {paiement.get_statut_display()}'}, status=400)
            
            paiement.statut = 'refuse'
            paiement.date_refus = timezone.now()
            paiement.refuse_par = request.user
            paiement.raison_refus = raison
            paiement.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Paiement {paiement.reference_paiement} refusé',
                'new_status': 'refuse',
                'new_status_display': 'Refusé'
            })
            
        elif action == 'annuler':
            raison = request.POST.get('raison', '').strip()
            if not raison:
                return JsonResponse({'error': 'Raison de l\'annulation requise'}, status=400)
            
            paiement.statut = 'annule'
            paiement.date_annulation = timezone.now()
            paiement.annule_par = request.user
            paiement.raison_annulation = raison
            paiement.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Paiement {paiement.reference_paiement} annulé',
                'new_status': 'annule',
                'new_status_display': 'Annulé'
            })
    
    except Exception as e:
        logger.error(f"Erreur lors de l'action {action} sur paiement {pk}: {e}")
        return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)
