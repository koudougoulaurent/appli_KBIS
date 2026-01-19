"""
Vues CRUD dédiées aux paiements partiels pour les utilisateurs PRIVILEGE
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import Paiement
from .forms import PaiementForm
from core.utils import check_group_permissions, get_context_with_entreprise_config
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType


@login_required
def modifier_paiement_partiel(request, paiement_id):
    """
    Modifier un paiement partiel existant
    Réservé aux utilisateurs PRIVILEGE
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_contrats_paiements_partiels')
    
    # Récupérer le paiement
    paiement = get_object_or_404(
        Paiement,
        pk=paiement_id,
        est_paiement_partiel=True,
        is_deleted=False
    )
    
    # Sauvegarder les anciennes données pour l'audit
    old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    
    if request.method == 'POST':
        form = PaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarder l'ancien statut
                    ancien_statut = paiement.statut
                    ancien_montant = paiement.montant
                    ancien_montant_restant = paiement.montant_restant_du
                    
                    # Sauvegarder le paiement modifié
                    paiement_modifie = form.save(commit=False)
                    paiement_modifie.date_modification = timezone.now()
                    paiement_modifie.save()
                    
                    # Si le montant a changé, recalculer le montant restant
                    if ancien_montant != paiement_modifie.montant:
                        from .services_paiement_partiel import ServicePaiementPartiel
                        ServicePaiementPartiel.synchroniser_paiement_partiel(paiement_modifie)
                    
                    # Vérifier si la modification complète un reliquat
                    if ancien_statut != 'valide' and paiement_modifie.statut == 'valide':
                        from .services_paiement_partiel import ServicePaiementPartiel
                        ServicePaiementPartiel.verifier_et_completer_reliquat(
                            paiement=paiement_modifie,
                            skip_save=False
                        )
                    
                    # Log d'audit
                    new_data = {f.name: getattr(paiement_modifie, f.name) for f in paiement_modifie._meta.fields}
                    AuditLog.objects.create(
                        content_type=ContentType.objects.get_for_model(Paiement),
                        object_id=paiement_modifie.pk,
                        action='UPDATE',
                        old_data=old_data,
                        new_data=new_data,
                        user=request.user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(
                        request,
                        f"✅ Paiement partiel modifié avec succès ! "
                        f"Nouveau montant: {paiement_modifie.montant:,.0f} F CFA"
                    )
                    
                    return redirect('paiements:liste_contrats_paiements_partiels')
                    
            except Exception as e:
                messages.error(request, f"❌ Erreur lors de la modification : {str(e)}")
                return redirect('paiements:modifier_paiement_partiel', paiement_id=paiement_id)
    else:
        form = PaiementForm(instance=paiement)
    
    # Calculer les informations de contexte
    from .services_paiement_partiel import ServicePaiementPartiel
    calcul = ServicePaiementPartiel.calculer_montant_restant(
        paiement.contrat,
        paiement.mois_paye
    )
    
    context = get_context_with_entreprise_config({
        'form': form,
        'paiement': paiement,
        'calcul': calcul,
        'contrat': paiement.contrat,
        'title': f'Modifier le Paiement Partiel - {paiement.contrat.numero_contrat}',
        'mode': 'edit'
    })
    
    return render(request, 'paiements/modifier_paiement_partiel.html', context)


@login_required
@require_POST
def supprimer_paiement_partiel(request, paiement_id):
    """
    Supprimer (logiquement) un paiement partiel
    Réservé aux utilisateurs PRIVILEGE
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        return JsonResponse({
            'success': False,
            'message': permissions['message']
        }, status=403)
    
    try:
        # Récupérer le paiement
        paiement = get_object_or_404(
            Paiement,
            pk=paiement_id,
            est_paiement_partiel=True,
            is_deleted=False
        )
        
        # Sauvegarder les données pour l'audit
        old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
        
        with transaction.atomic():
            # Suppression logique
            paiement.is_deleted = True
            paiement.deleted_at = timezone.now()
            paiement.deleted_by = request.user
            paiement.save()
            
            # Recalculer les montants restants pour les autres paiements du même mois
            from .services_paiement_partiel import ServicePaiementPartiel
            autres_paiements = Paiement.objects.filter(
                contrat=paiement.contrat,
                mois_paye=paiement.mois_paye,
                is_deleted=False,
                est_paiement_partiel=True
            ).exclude(pk=paiement_id)
            
            for autre_paiement in autres_paiements:
                ServicePaiementPartiel.synchroniser_paiement_partiel(autre_paiement)
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Paiement),
                object_id=paiement.pk,
                action='DELETE',
                old_data=old_data,
                new_data=None,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                request,
                f"✅ Paiement partiel supprimé avec succès ! "
                f"Montant: {paiement.montant:,.0f} F CFA"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Paiement partiel supprimé avec succès',
                'redirect_url': '/paiements/paiements-partiels/contrats/'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la suppression : {str(e)}'
        }, status=500)


@login_required
def detail_paiement_partiel(request, paiement_id):
    """
    Afficher les détails d'un paiement partiel
    """
    paiement = get_object_or_404(
        Paiement,
        pk=paiement_id,
        est_paiement_partiel=True,
        is_deleted=False
    )
    
    # Calculer les informations contextuelles
    from .services_paiement_partiel import ServicePaiementPartiel
    
    calcul = ServicePaiementPartiel.calculer_montant_restant(
        paiement.contrat,
        paiement.mois_paye
    )
    
    # Récupérer tous les paiements partiels pour ce mois
    paiements_du_mois = Paiement.objects.filter(
        contrat=paiement.contrat,
        mois_paye=paiement.mois_paye,
        is_deleted=False,
        est_paiement_partiel=True,
        statut__in=['valide', 'en_attente']
    ).order_by('date_paiement')
    
    # Calculer la position du paiement dans la séquence
    position = 1
    for idx, p in enumerate(paiements_du_mois, start=1):
        if p.id == paiement.id:
            position = idx
            break
    
    # Vérifier les permissions pour l'édition
    permissions_edit = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'change')
    permissions_delete = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    
    context = get_context_with_entreprise_config({
        'paiement': paiement,
        'calcul': calcul,
        'paiements_du_mois': paiements_du_mois,
        'position': position,
        'total_paiements_mois': paiements_du_mois.count(),
        'can_edit': permissions_edit['allowed'],
        'can_delete': permissions_delete['allowed'],
        'title': f'Détail Paiement Partiel - {paiement.contrat.numero_contrat}'
    })
    
    return render(request, 'paiements/detail_paiement_partiel.html', context)
