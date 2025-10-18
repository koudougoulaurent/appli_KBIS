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
    """Liste des contrats avec actions rapides optimisées"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Récupérer les filtres
    query = request.GET.get('q', '')
    statut_filter = request.GET.get('statut', '')
    bailleur_filter = request.GET.get('bailleur', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    # Base QuerySet avec annotations optimisées
    from django.db.models import Sum, Count, F, Case, When, DecimalField, Q
    
    contrats = Contrat.objects.select_related(
        'propriete', 'locataire', 'propriete__bailleur'
    ).annotate(
        # Loyer total formaté
        loyer_total_formatted=Case(
            When(loyer_mensuel__isnull=False, then='loyer_mensuel'),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        # Nom complet du locataire
        locataire_nom_complet=Case(
            When(locataire__nom__isnull=False, 
                 locataire__prenom__isnull=False,
                 then=F('locataire__nom') + ' ' + F('locataire__prenom')),
            When(locataire__nom__isnull=False,
                 then=F('locataire__nom')),
            default='Locataire inconnu',
            output_field=models.CharField(max_length=200)
        ),
        # Adresse complète de la propriété
        propriete_adresse_complete=Case(
            When(propriete__adresse__isnull=False,
                 propriete__ville__isnull=False,
                 then=F('propriete__adresse') + ', ' + F('propriete__ville')),
            When(propriete__adresse__isnull=False,
                 then=F('propriete__adresse')),
            default='Adresse non renseignée',
            output_field=models.CharField(max_length=300)
        ),
        # Statut calculé
        statut_calcule=Case(
            When(est_resilie=True, then='Résilié'),
            When(est_actif=True, then='Actif'),
            default='Inactif',
            output_field=models.CharField(max_length=20)
        )
    ).order_by('-date_creation')
    
    # Recherche optimisée
    if query:
        contrats = contrats.filter(
            Q(numero_contrat__icontains=query) |
            Q(locataire__nom__icontains=query) |
            Q(locataire__prenom__icontains=query) |
            Q(propriete__titre__icontains=query) |
            Q(propriete__adresse__icontains=query) |
            Q(propriete__ville__icontains=query) |
            Q(notes__icontains=query)
        )
    
    # Filtres optimisés
    if statut_filter:
        if statut_filter == 'actif':
            contrats = contrats.filter(est_actif=True, est_resilie=False)
        elif statut_filter == 'resilie':
            contrats = contrats.filter(est_resilie=True)
        elif statut_filter == 'inactif':
            contrats = contrats.filter(est_actif=False, est_resilie=False)
    
    if bailleur_filter:
        contrats = contrats.filter(propriete__bailleur_id=bailleur_filter)
    
    # Filtres de dates
    if date_debut:
        contrats = contrats.filter(date_debut__gte=date_debut)
    
    if date_fin:
        contrats = contrats.filter(date_debut__lte=date_fin)
    
    # Calcul des statistiques avec requêtes optimisées
    total_contrats = contrats.count()
    
    # Statistiques détaillées
    stats = {
        'total': total_contrats,
        'actifs': contrats.filter(est_actif=True, est_resilie=False).count(),
        'resilies': contrats.filter(est_resilie=True).count(),
        'inactifs': contrats.filter(est_actif=False, est_resilie=False).count(),
        'loyer_total': contrats.aggregate(
            total=Sum('loyer_mensuel')
        )['total'] or 0,
    }
    
    # Statistiques par bailleur
    stats_par_bailleur = contrats.values(
        'propriete__bailleur__nom', 'propriete__bailleur__prenom'
    ).annotate(
        count=Count('id'),
        loyer_total=Sum('loyer_mensuel')
    ).order_by('propriete__bailleur__nom')
    
    # Pagination
    paginator = Paginator(contrats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtres pour le formulaire
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.all()
    
    context = {
        'page_obj': page_obj,
        'contrats': page_obj,
        'stats': stats,
        'stats_par_bailleur': stats_par_bailleur,
        'bailleurs': bailleurs,
        'query': query,
        'statut_filter': statut_filter,
        'bailleur_filter': bailleur_filter,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'label': 'Contrats'}
        ],
        'filtres_actifs': {
            'query': query,
            'statut': statut_filter,
            'bailleur': bailleur_filter,
            'date_debut': date_debut,
            'date_fin': date_fin,
        }
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_dashboard(request)
    
    return render(request, 'contrats/liste_contrats.html', context)
