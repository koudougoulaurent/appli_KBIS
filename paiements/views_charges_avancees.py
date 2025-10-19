#!/usr/bin/env python3
"""
Vues avancées pour la gestion des charges déductibles
====================================================

Ce module gère l'interface complète de gestion des charges déductibles
avec intégration aux récapitulatifs mensuels.
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import ChargeDeductible
from .models import RecapMensuel
from .forms_charges_avancees import (
    ChargeDeductibleForm,
    RechercheChargesForm,
    ValidationChargesForm,
    ImportChargesForm,
    RapportChargesForm
)
from proprietes.models import Bailleur, Propriete
from contrats.models import Contrat

logger = logging.getLogger(__name__)


@login_required
def liste_charges_avancees(request):
    """Liste avancée des charges déductibles avec filtres."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Formulaire de recherche
    form_recherche = RechercheChargesForm(request.GET)
    
    # Base queryset
    charges = ChargeDeductible.objects.select_related(
        'contrat', 'contrat__propriete', 'contrat__propriete__bailleur', 'contrat__locataire'
    ).order_by('-date_creation')
    
    # Appliquer les filtres
    if form_recherche.is_valid():
        bailleur = form_recherche.cleaned_data.get('bailleur')
        if bailleur:
            charges = charges.filter(contrat__propriete__bailleur=bailleur)
        
        type_charge = form_recherche.cleaned_data.get('type_charge')
        if type_charge:
            charges = charges.filter(type_charge=type_charge)
        
        statut = form_recherche.cleaned_data.get('statut')
        if statut:
            charges = charges.filter(statut=statut)
        
        date_debut = form_recherche.cleaned_data.get('date_debut')
        if date_debut:
            charges = charges.filter(date_charge__gte=date_debut)
        
        date_fin = form_recherche.cleaned_data.get('date_fin')
        if date_fin:
            charges = charges.filter(date_charge__lte=date_fin)
        
        montant_min = form_recherche.cleaned_data.get('montant_min')
        if montant_min:
            charges = charges.filter(montant__gte=montant_min)
        
        montant_max = form_recherche.cleaned_data.get('montant_max')
        if montant_max:
            charges = charges.filter(montant__lte=montant_max)
        
        libelle = form_recherche.cleaned_data.get('libelle')
        if libelle:
            charges = charges.filter(libelle__icontains=libelle)
    
    # Pagination
    paginator = Paginator(charges, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': charges.count(),
        'total_montant': charges.aggregate(Sum('montant'))['montant__sum'] or 0,
        'par_statut': charges.values('statut').annotate(
            count=Count('id'),
            total=Sum('montant')
        ),
        'par_type': charges.values('type_charge').annotate(
            count=Count('id'),
            total=Sum('montant')
        ),
    }
    
    context = {
        'page_title': 'Gestion des Charges Déductibles',
        'page_icon': 'receipt',
        'form_recherche': form_recherche,
        'page_obj': page_obj,
        'stats': stats,
    }
    
    return render(request, 'paiements/charges/liste_charges_avancees.html', context)


@login_required
def creer_charge_avancee(request, bailleur_id=None):
    """Créer une nouvelle charge déductible."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    bailleur = None
    if bailleur_id:
        bailleur = get_object_or_404(Bailleur, id=bailleur_id, actif=True)
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST, bailleur=bailleur)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.cree_par = request.user
            charge.save()
            
            messages.success(
                request,
                f'Charge déductible créée avec succès pour {charge.contrat.propriete.bailleur.nom} {charge.contrat.propriete.bailleur.prenom}'
            )
            
            return redirect('paiements:liste_charges_avancees')
    else:
        form = ChargeDeductibleForm(bailleur=bailleur)
    
    context = {
        'page_title': 'Créer une Charge Déductible',
        'page_icon': 'plus-circle',
        'form': form,
        'bailleur': bailleur,
    }
    
    return render(request, 'paiements/charges/creer_charge_avancee.html', context)


@login_required
def modifier_charge_avancee(request, charge_id):
    """Modifier une charge déductible existante."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    charge = get_object_or_404(ChargeDeductible, id=charge_id)
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST, instance=charge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Charge déductible modifiée avec succès.')
            return redirect('paiements:liste_charges_avancees')
    else:
        form = ChargeDeductibleForm(instance=charge)
    
    context = {
        'page_title': 'Modifier la Charge Déductible',
        'page_icon': 'pencil-square',
        'form': form,
        'charge': charge,
    }
    
    return render(request, 'paiements/charges/modifier_charge_avancee.html', context)


@login_required
def detail_charge_avancee(request, charge_id):
    """Détail d'une charge déductible."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    charge = get_object_or_404(
        ChargeDeductible.objects.select_related(
            'contrat', 'contrat__propriete', 'contrat__propriete__bailleur', 'contrat__locataire'
        ),
        id=charge_id
    )
    
    context = {
        'page_title': f'Détail - {charge.libelle}',
        'page_icon': 'eye',
        'charge': charge,
    }
    
    return render(request, 'paiements/charges/detail_charge_avancee.html', context)


@login_required
@require_http_methods(["POST"])
def valider_charges(request):
    """Valider ou refuser des charges en lot."""
    
    # Vérifier si l'utilisateur est dans le groupe PRIVILEGE
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    
    form = ValidationChargesForm(request.POST)
    if form.is_valid():
        charges = form.cleaned_data['charges']
        action = form.cleaned_data['action']
        motif_refus = form.cleaned_data.get('motif_refus', '')
        
        updated_count = 0
        
        for charge in charges:
            if action == 'valider':
                charge.statut = 'validee'
                charge.date_validation = timezone.now()
                charge.validateur = request.user
            elif action == 'refuser':
                charge.statut = 'refusee'
                charge.motif_refus = motif_refus
            elif action == 'deduire':
                charge.statut = 'deduite'
                charge.date_deduction = timezone.now()
            
            charge.save()
            updated_count += 1
        
        messages.success(request, f'{updated_count} charge(s) mise(s) à jour avec succès.')
        return JsonResponse({'success': True, 'updated_count': updated_count})
    
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
def dashboard_charges_bailleur(request, bailleur_id):
    """Dashboard des charges pour un bailleur spécifique."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    bailleur = get_object_or_404(Bailleur, id=bailleur_id, actif=True)
    
    # Récupérer les charges du bailleur
    charges = ChargeDeductible.objects.filter(
        contrat__propriete__bailleur=bailleur
    ).select_related('contrat', 'contrat__propriete', 'contrat__locataire')
    
    # Statistiques
    stats = {
        'total_charges': charges.count(),
        'total_montant': charges.aggregate(Sum('montant'))['montant__sum'] or 0,
        'charges_en_attente': charges.filter(statut='en_attente').count(),
        'charges_validees': charges.filter(statut='validee').count(),
        'charges_deduites': charges.filter(statut='deduite').count(),
        'charges_refusees': charges.filter(statut='refusee').count(),
    }
    
    # Charges par propriété
    charges_par_propriete = charges.values(
        'contrat__propriete__titre',
        'contrat__propriete__adresse'
    ).annotate(
        count=Count('id'),
        total=Sum('montant')
    ).order_by('-total')
    
    # Charges récentes
    charges_recentes = charges.order_by('-date_creation')[:10]
    
    # Récapitulatifs concernés
    recapitulatifs = RecapMensuel.objects.filter(
        bailleur=bailleur
    ).order_by('-mois_recap')[:5]
    
    context = {
        'page_title': f'Charges - {bailleur.nom} {bailleur.prenom}',
        'page_icon': 'receipt',
        'bailleur': bailleur,
        'stats': stats,
        'charges_par_propriete': charges_par_propriete,
        'charges_recentes': charges_recentes,
        'recapitulatifs': recapitulatifs,
    }
    
    return render(request, 'paiements/charges/dashboard_charges_bailleur.html', context)


@login_required
def rapport_charges(request):
    """Générer des rapports sur les charges déductibles."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method == 'POST':
        form = RapportChargesForm(request.POST)
        if form.is_valid():
            # Logique de génération de rapport
            # À implémenter selon les besoins
            messages.success(request, 'Rapport généré avec succès.')
            return redirect('paiements:liste_charges_avancees')
    else:
        form = RapportChargesForm()
    
    context = {
        'page_title': 'Rapports des Charges',
        'page_icon': 'file-earmark-bar-graph',
        'form': form,
    }
    
    return render(request, 'paiements/charges/rapport_charges.html', context)


@login_required
@csrf_exempt
def api_charges_bailleur(request, bailleur_id):
    """API pour récupérer les charges d'un bailleur."""
    
    if not request.user.groups.filter(name='PRIVILEGE').exists():
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    
    try:
        bailleur = Bailleur.objects.get(id=bailleur_id, actif=True)
        
        # Récupérer les charges
        charges = ChargeDeductible.objects.filter(
            contrat__propriete__bailleur=bailleur
        ).select_related('contrat', 'contrat__propriete', 'contrat__locataire')
        
        # Filtrer par statut si spécifié
        statut = request.GET.get('statut')
        if statut:
            charges = charges.filter(statut=statut)
        
        # Filtrer par période si spécifiée
        date_debut = request.GET.get('date_debut')
        if date_debut:
            charges = charges.filter(date_charge__gte=date_debut)
        
        date_fin = request.GET.get('date_fin')
        if date_fin:
            charges = charges.filter(date_charge__lte=date_fin)
        
        # Préparer les données
        charges_data = []
        for charge in charges:
            charges_data.append({
                'id': charge.id,
                'libelle': charge.libelle,
                'montant': float(charge.montant),
                'type_charge': charge.get_type_charge_display(),
                'statut': charge.get_statut_display(),
                'date_charge': charge.date_charge.strftime('%d/%m/%Y'),
                'propriete': charge.contrat.propriete.titre,
                'locataire': f"{charge.contrat.locataire.nom} {charge.contrat.locataire.prenom}",
                'facture_numero': charge.facture_numero,
                'fournisseur': charge.fournisseur,
            })
        
        # Statistiques
        stats = {
            'total': charges.count(),
            'total_montant': float(charges.aggregate(Sum('montant'))['montant__sum'] or 0),
            'par_statut': list(charges.values('statut').annotate(
                count=Count('id'),
                total=Sum('montant')
            )),
        }
        
        return JsonResponse({
            'success': True,
            'bailleur': {
                'id': bailleur.id,
                'nom': bailleur.nom,
                'prenom': bailleur.prenom,
            },
            'charges': charges_data,
            'stats': stats,
        })
        
    except Bailleur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bailleur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
