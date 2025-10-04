"""
Vues pour l'intégration des charges dans les retraits
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from decimal import Decimal

from core.utils import check_group_permissions_with_fallback
from proprietes.models import ChargesBailleur
from paiements.models import RetraitBailleur
from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent


@login_required
def integrer_charges_retrait(request, retrait_id):
    """
    Intègre automatiquement toutes les charges bailleur dans un retrait existant.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'modify'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    # Récupérer le retrait
    retrait = get_object_or_404(RetraitBailleur, pk=retrait_id, is_deleted=False)
    
    # Vérifier que le retrait peut être modifié
    if retrait.statut not in ['en_attente']:
        messages.error(request, 'Ce retrait ne peut plus être modifié.')
        return redirect('paiements:retrait_detail', pk=retrait_id)
    
    try:
        # Utiliser le service intelligent pour intégrer les charges
        resultat = ServiceChargesBailleurIntelligent.integrer_charges_dans_retrait(
            retrait, retrait.mois_retrait
        )
        
        if resultat.get('erreur'):
            messages.error(request, f'Erreur lors de l\'intégration: {resultat["erreur"]}')
        else:
            total_charges = resultat.get('total_charges', Decimal('0'))
            charges_details = resultat.get('charges_details', [])
            
            if total_charges > 0:
                messages.success(
                    request, 
                    f'Intégration réussie ! {len(charges_details)} charges intégrées '
                    f'pour un total de {total_charges} F CFA déduit du retrait.'
                )
            else:
                messages.info(request, 'Aucune charge à intégrer pour ce mois.')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'intégration des charges: {str(e)}')
        return redirect('paiements:retrait_detail', pk=retrait_id)
    
    return redirect('paiements:retrait_detail', pk=retrait_id)


@login_required
def integrer_charge_specifique(request, retrait_id, charge_id):
    """
    Intègre une charge spécifique dans un retrait existant.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'modify'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    # Récupérer le retrait et la charge
    retrait = get_object_or_404(RetraitBailleur, pk=retrait_id, is_deleted=False)
    charge = get_object_or_404(ChargesBailleur, pk=charge_id)
    
    # Vérifier que le retrait peut être modifié
    if retrait.statut not in ['en_attente']:
        messages.error(request, 'Ce retrait ne peut plus être modifié.')
        return redirect('paiements:retrait_detail', pk=retrait_id)
    
    # Vérifier que la charge appartient au même bailleur
    if charge.propriete.bailleur != retrait.bailleur:
        messages.error(request, 'Cette charge n\'appartient pas au bailleur de ce retrait.')
        return redirect('paiements:retrait_detail', pk=retrait_id)
    
    # Vérifier que la charge peut être déduite
    if charge.statut not in ['en_attente', 'deduite_retrait']:
        messages.error(request, 'Cette charge ne peut pas être déduite.')
        return redirect('paiements:retrait_detail', pk=retrait_id)
    
    try:
        # Calculer le montant déductible
        montant_deductible = charge.get_montant_deductible()
        
        if montant_deductible <= 0:
            messages.warning(request, 'Aucun montant déductible pour cette charge.')
            return redirect('paiements:retrait_detail', pk=retrait_id)
        
        # Marquer la charge comme déduite
        montant_effectivement_deduit = charge.marquer_comme_deduit(montant_deductible)
        
        if montant_effectivement_deduit > 0:
            # Mettre à jour le retrait
            retrait.montant_charges_bailleur += Decimal(str(montant_effectivement_deduit))
            retrait.montant_net_a_payer = retrait.montant_loyers_bruts - retrait.montant_charges_deductibles - retrait.montant_charges_bailleur
            retrait.save()
            
            messages.success(
                request, 
                f'Charge "{charge.titre}" intégrée avec succès ! '
                f'Montant déduit: {montant_effectivement_deduit} F CFA'
            )
        else:
            messages.warning(request, 'Aucun montant n\'a pu être déduit.')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'intégration de la charge: {str(e)}')
    
    return redirect('paiements:retrait_detail', pk=retrait_id)


@login_required
def retirer_charge_retrait(request, retrait_id, charge_id):
    """
    Retire une charge d'un retrait (annule la déduction).
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'modify'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    # Récupérer le retrait et la charge
    retrait = get_object_or_404(RetraitBailleur, pk=retrait_id, is_deleted=False)
    charge = get_object_or_404(ChargesBailleur, pk=charge_id)
    
    # Vérifier que le retrait peut être modifié
    if retrait.statut not in ['en_attente']:
        messages.error(request, 'Ce retrait ne peut plus être modifié.')
        return redirect('paiements:retrait_detail', pk=retrait_id)
    
    try:
        # Récupérer le montant déjà déduit
        montant_deja_deduit = charge.montant_deja_deduit
        
        if montant_deja_deduit <= 0:
            messages.warning(request, 'Cette charge n\'a pas été déduite de ce retrait.')
            return redirect('paiements:retrait_detail', pk=retrait_id)
        
        # Annuler la déduction
        charge.montant_deja_deduit = Decimal('0')
        charge.montant_restant = charge.montant
        charge.statut = 'en_attente'
        charge.save()
        
        # Mettre à jour le retrait
        retrait.montant_charges_bailleur -= montant_deja_deduit
        retrait.montant_net_a_payer = retrait.montant_loyers_bruts - retrait.montant_charges_deductibles - retrait.montant_charges_bailleur
        retrait.save()
        
        messages.success(
            request, 
            f'Charge "{charge.titre}" retirée du retrait avec succès ! '
            f'Montant remis: {montant_deja_deduit} F CFA'
        )
        
    except Exception as e:
        messages.error(request, f'Erreur lors du retrait de la charge: {str(e)}')
    
    return redirect('paiements:retrait_detail', pk=retrait_id)


@login_required
def ajax_charges_disponibles(request, retrait_id):
    """
    API AJAX pour récupérer les charges disponibles pour un retrait.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'view'
    )
    
    if not permissions['allowed']:
        return JsonResponse({'error': 'Permissions insuffisantes'}, status=403)
    
    try:
        retrait = get_object_or_404(RetraitBailleur, pk=retrait_id, is_deleted=False)
        
        # Récupérer les charges disponibles pour le mois du retrait
        charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
            retrait.bailleur, retrait.mois_retrait
        )
        
        charges_info = []
        for detail in charges_data.get('charges_details', []):
            charge = detail['charge']
            charges_info.append({
                'id': charge.id,
                'titre': charge.titre,
                'type': charge.get_type_charge_display(),
                'montant': float(charge.montant),
                'montant_deductible': float(detail['montant_deductible']),
                'statut': charge.get_statut_display(),
                'date_charge': charge.date_charge.strftime('%d/%m/%Y'),
                'propriete': charge.propriete.nom
            })
        
        return JsonResponse({
            'charges': charges_info,
            'total_charges': float(charges_data.get('total_charges', 0)),
            'nombre_charges': len(charges_info)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
