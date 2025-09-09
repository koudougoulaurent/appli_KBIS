"""
Vues avec actions rapides pour le module Contrats
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

from .models import Contrat, Quittance, EtatLieux
from core.quick_actions_generator import QuickActionsGenerator
from core.utils import check_group_permissions

@login_required
def detail_contrat(request, pk):
    """Vue détaillée d'un contrat avec actions rapides"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    # Récupérer les paiements associés
    paiements = contrat.paiements.all().order_by('-date_paiement')[:10]
    
    # Récupérer les quittances
    quittances = contrat.quittances.all().order_by('-date_creation')[:5]
    
    # Récupérer les états des lieux
    etats_lieux = contrat.etats_lieux.all().order_by('-date_creation')[:5]
    
    # Statistiques
    stats = {
        'total_paiements': paiements.count(),
        'montant_total': paiements.aggregate(total=Sum('montant'))['total'] or 0,
        'paiements_en_attente': paiements.filter(statut='en_attente').count(),
        'quittances': quittances.count(),
        'etats_lieux': etats_lieux.count(),
    }
    
    context = {
        'contrat': contrat,
        'paiements': paiements,
        'quittances': quittances,
        'etats_lieux': etats_lieux,
        'stats': stats,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'contrats:liste', 'label': 'Contrats'},
            {'label': contrat.numero_contrat}
        ]
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_contrat(contrat, request)
    
    return render(request, 'contrats/detail_contrat.html', context)

@login_required
def liste_contrats(request):
    """Liste des contrats avec actions rapides"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    contrats = Contrat.objects.all().order_by('-date_creation')
    
    # Recherche
    query = request.GET.get('q', '')
    if query:
        contrats = contrats.filter(
            Q(numero_contrat__icontains=query) |
            Q(locataire__nom__icontains=query) |
            Q(propriete__titre__icontains=query)
        )
    
    # Filtres
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        contrats = contrats.filter(statut=statut_filter)
    
    # Pagination
    paginator = Paginator(contrats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': contrats.count(),
        'actifs': contrats.filter(est_actif=True).count(),
        'resilies': contrats.filter(est_resilie=True).count(),
        'en_attente': contrats.filter(statut='en_attente').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'contrats': page_obj,
        'stats': stats,
        'query': query,
        'statut_filter': statut_filter,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'label': 'Contrats'}
        ]
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_dashboard(request)
    
    return render(request, 'contrats/liste_contrats.html', context)
