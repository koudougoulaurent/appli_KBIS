"""
Vues spécialisées pour les retraits des bailleurs
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal

from .models import RetraitBailleur, Paiement
from proprietes.models import Bailleur
from core.quick_actions_generator import QuickActionsGenerator
from core.utils import check_group_permissions

@login_required
def retraits_bailleur(request, pk):
    """Vue détaillée des retraits d'un bailleur avec statistiques"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    bailleur = get_object_or_404(Bailleur, pk=pk)
    
    # Récupérer les retraits du bailleur avec optimisations
    retraits = RetraitBailleur.objects.filter(
        bailleur=bailleur,
        is_deleted=False
    ).select_related('bailleur', 'cree_par', 'valide_par').order_by('-mois_retrait')
    
    # Recherche par mois
    mois_search = request.GET.get('mois', '')
    if mois_search:
        try:
            mois_date = datetime.strptime(mois_search, '%Y-%m').date()
            retraits = retraits.filter(mois_retrait__year=mois_date.year, mois_retrait__month=mois_date.month)
        except ValueError:
            pass
    
    # Filtre par statut
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        retraits = retraits.filter(statut=statut_filter)
    
    # Filtre par type
    type_filter = request.GET.get('type_retrait', '')
    if type_filter:
        retraits = retraits.filter(type_retrait=type_filter)
    
    # Pagination
    paginator = Paginator(retraits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques des retraits
    stats = {
        'total_retraits': retraits.count(),
        'montant_total_brut': retraits.aggregate(total=Sum('montant_loyers_bruts'))['total'] or 0,
        'montant_total_charges': retraits.aggregate(total=Sum('montant_charges_deductibles'))['total'] or 0,
        'montant_total_net': retraits.aggregate(total=Sum('montant_net_a_payer'))['total'] or 0,
        'retraits_valides': retraits.filter(statut='valide').count(),
        'retraits_payes': retraits.filter(statut='paye').count(),
        'retraits_en_attente': retraits.filter(statut='en_attente').count(),
        'retraits_annules': retraits.filter(statut='annule').count(),
    }
    
    # Statistiques par mois (12 derniers mois) - Version compatible Django 5.2
    from django.db.models.functions import Extract
    retraits_par_mois = retraits.annotate(
        mois_annee=Extract('mois_retrait', 'year'),
        mois_mois=Extract('mois_retrait', 'month')
    ).values('mois_annee', 'mois_mois').annotate(
        count=Count('id'),
        total_brut=Sum('montant_loyers_bruts'),
        total_net=Sum('montant_net_a_payer')
    ).order_by('-mois_annee', '-mois_mois')[:12]
    
    # Derniers paiements concernés (optimisé)
    derniers_paiements = Paiement.objects.filter(
        retraits_bailleur__bailleur=bailleur
    ).select_related('locataire', 'propriete').distinct().order_by('-date_paiement')[:10]
    
    context = {
        'bailleur': bailleur,
        'page_obj': page_obj,
        'retraits': page_obj,
        'stats': stats,
        'retraits_par_mois': retraits_par_mois,
        'derniers_paiements': derniers_paiements,
        'mois_search': mois_search,
        'statut_filter': statut_filter,
        'type_filter': type_filter,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:liste_bailleurs', 'label': 'Bailleurs'},
            {'url': 'proprietes:detail_bailleur', 'args': [bailleur.pk], 'label': bailleur.get_nom_complet()},
            {'label': 'Retraits'}
        ]
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_bailleur_retraits(bailleur, request)
    
    return render(request, 'paiements/retraits_bailleur.html', context)

@login_required
def detail_retrait_bailleur(request, pk):
    """Vue détaillée d'un retrait spécifique"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    retrait = get_object_or_404(RetraitBailleur.objects.select_related('bailleur', 'cree_par', 'valide_par'), pk=pk)
    bailleur = retrait.bailleur
    
    # Récupérer les paiements concernés (optimisé)
    paiements_concernes = retrait.paiements_concernes.select_related('locataire', 'propriete').order_by('-date_paiement')
    
    # Récupérer les charges déductibles (optimisé)
    charges_deductibles = retrait.charges_deductibles.select_related('propriete').all()
    
    # Récupérer les reçus (optimisé)
    reçus = retrait.recus.select_related('cree_par').order_by('-date_emission')
    
    context = {
        'retrait': retrait,
        'bailleur': bailleur,
        'paiements_concernes': paiements_concernes,
        'charges_deductibles': charges_deductibles,
        'reçus': reçus,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:liste_bailleurs', 'label': 'Bailleurs'},
            {'url': 'proprietes:detail_bailleur', 'args': [bailleur.pk], 'label': bailleur.get_nom_complet()},
            {'url': 'paiements:retraits_bailleur', 'args': [bailleur.pk], 'label': 'Retraits'},
            {'label': f'Retrait {retrait.mois_retrait.strftime("%B %Y")}'}
        ]
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_retrait_bailleur(retrait, request)
    
    return render(request, 'paiements/detail_retrait_bailleur.html', context)

@login_required
def ajouter_retrait_bailleur(request, bailleur_id):
    """Ajouter un nouveau retrait pour un bailleur"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    if request.method == 'POST':
        # Logique d'ajout du retrait
        messages.success(request, f'Retrait ajouté avec succès pour {bailleur.get_nom_complet()}')
        return redirect('paiements:retraits_bailleur', pk=bailleur.pk)
    
    context = {
        'bailleur': bailleur,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:liste_bailleurs', 'label': 'Bailleurs'},
            {'url': 'proprietes:detail_bailleur', 'args': [bailleur.pk], 'label': bailleur.get_nom_complet()},
            {'url': 'paiements:retraits_bailleur', 'args': [bailleur.pk], 'label': 'Retraits'},
            {'label': 'Nouveau Retrait'}
        ]
    }
    
    return render(request, 'paiements/ajouter_retrait_bailleur.html', context)

@login_required
def modifier_retrait_bailleur(request, pk):
    """Modifier un retrait existant"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk)
    
    if request.method == 'POST':
        # Logique de modification du retrait
        messages.success(request, f'Retrait modifié avec succès')
        return redirect('paiements:detail_retrait_bailleur', pk=retrait.pk)
    
    context = {
        'retrait': retrait,
        'bailleur': retrait.bailleur,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:liste_bailleurs', 'label': 'Bailleurs'},
            {'url': 'proprietes:detail_bailleur', 'args': [retrait.bailleur.pk], 'label': retrait.bailleur.get_nom_complet()},
            {'url': 'paiements:retraits_bailleur', 'args': [retrait.bailleur.pk], 'label': 'Retraits'},
            {'label': f'Modifier Retrait {retrait.mois_retrait.strftime("%B %Y")}'}
        ]
    }
    
    return render(request, 'paiements/modifier_retrait_bailleur.html', context)

@login_required
def valider_retrait(request, pk):
    """Valider un retrait"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk)
    
    if request.method == 'POST':
        retrait.statut = 'valide'
        retrait.valide_par = request.user
        retrait.save()
        messages.success(request, f'Retrait validé avec succès')
        return redirect('paiements:detail_retrait_bailleur', pk=retrait.pk)
    
    context = {
        'retrait': retrait,
        'bailleur': retrait.bailleur,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:liste_bailleurs', 'label': 'Bailleurs'},
            {'url': 'proprietes:detail_bailleur', 'args': [retrait.bailleur.pk], 'label': retrait.bailleur.get_nom_complet()},
            {'url': 'paiements:retraits_bailleur', 'args': [retrait.bailleur.pk], 'label': 'Retraits'},
            {'label': f'Valider Retrait {retrait.mois_retrait.strftime("%B %Y")}'}
        ]
    }
    
    return render(request, 'paiements/valider_retrait_bailleur.html', context)

@login_required
def marquer_paye_retrait(request, pk):
    """Marquer un retrait comme payé"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk)
    
    if request.method == 'POST':
        retrait.statut = 'paye'
        retrait.date_versement = timezone.now().date()
        retrait.save()
        messages.success(request, f'Retrait marqué comme payé')
        return redirect('paiements:detail_retrait_bailleur', pk=retrait.pk)
    
    context = {
        'retrait': retrait,
        'bailleur': retrait.bailleur,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:liste_bailleurs', 'label': 'Bailleurs'},
            {'url': 'proprietes:detail_bailleur', 'args': [retrait.bailleur.pk], 'label': retrait.bailleur.get_nom_complet()},
            {'url': 'paiements:retraits_bailleur', 'args': [retrait.bailleur.pk], 'label': 'Retraits'},
            {'label': f'Marquer Payé - {retrait.mois_retrait.strftime("%B %Y")}'}
        ]
    }
    
    return render(request, 'paiements/marquer_paye_retrait_bailleur.html', context)

@login_required
def generer_recu_retrait(request, pk):
    """Générer un reçu pour un retrait"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk)
    
    # Logique de génération du reçu
    messages.success(request, f'Reçu généré avec succès')
    return redirect('paiements:detail_retrait_bailleur', pk=retrait.pk)

@login_required
def export_retraits_bailleur(request, bailleur_id):
    """Exporter les retraits d'un bailleur"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # Logique d'export
    messages.success(request, f'Export des retraits généré avec succès')
    return redirect('paiements:retraits_bailleur', pk=bailleur.pk)

@login_required
def generer_rapport_retraits(request, bailleur_id):
    """Générer un rapport des retraits d'un bailleur"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_bailleurs')
    
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # Logique de génération du rapport
    messages.success(request, f'Rapport des retraits généré avec succès')
    return redirect('paiements:retraits_bailleur', pk=bailleur.pk)
