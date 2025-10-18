"""
Vues avec actions rapides pour le module Paiements
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum

from .models import Paiement
from core.quick_actions_generator import QuickActionsGenerator
from core.utils import check_group_permissions
from proprietes.models import Locataire

@login_required
def detail_paiement(request, pk):
    """Vue détaillée d'un paiement avec actions rapides"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Récupérer les informations du contrat
    contrat = paiement.contrat
    locataire = contrat.locataire
    propriete = contrat.propriete
    
    # Statistiques
    stats = {
        'montant': paiement.montant,
        'statut': paiement.statut,
        'date_paiement': paiement.date_paiement,
        'methode_paiement': paiement.methode_paiement,
    }
    
    context = {
        'paiement': paiement,
        'contrat': contrat,
        'locataire': locataire,
        'propriete': propriete,
        'stats': stats,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'paiements:liste', 'label': 'Paiements'},
            {'label': paiement.reference_paiement}
        ]
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_paiement(paiement, request)
    
    return render(request, 'paiements/detail_paiement.html', context)

@login_required
def liste_paiements(request, locataire_id=None):
    """Liste des paiements avec actions rapides"""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Filtrer les paiements en excluant les cautions/avances non marquées comme payées
    from django.db.models import Q
    paiements = Paiement.objects.filter(is_deleted=False).exclude(
        # Exclure les paiements de caution qui ne sont pas marqués comme payés
        Q(type_paiement='depot_garantie') & Q(contrat__caution_payee=False)
    ).exclude(
        # Exclure les paiements d'avance qui ne sont pas marqués comme payés
        Q(type_paiement='avance') & Q(contrat__avance_loyer_payee=False)
    ).order_by('-date_paiement')
    locataire_obj = None
    
    # Filtre par locataire si spécifié via URL ou GET
    if locataire_id:
        try:
            locataire_obj = Locataire.objects.get(pk=locataire_id)
            paiements = paiements.filter(contrat__locataire=locataire_obj)
        except Locataire.DoesNotExist:
            messages.error(request, "Locataire introuvable.")
            return redirect('paiements:liste')
    else:
        # Fallback pour le paramètre GET (compatibilité)
        locataire_id = request.GET.get('locataire', '')
        if locataire_id:
            try:
                locataire_obj = Locataire.objects.get(pk=locataire_id)
                paiements = paiements.filter(contrat__locataire=locataire_obj)
            except Locataire.DoesNotExist:
                messages.error(request, "Locataire introuvable.")
                return redirect('paiements:liste')
    
    # Recherche
    query = request.GET.get('q', '')
    if query:
        paiements = paiements.filter(
            Q(reference_paiement__icontains=query) |
            Q(contrat__numero_contrat__icontains=query) |
            Q(contrat__locataire__nom__icontains=query)
        )
    
    # Filtres
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        paiements = paiements.filter(statut=statut_filter)
    
    type_filter = request.GET.get('type_paiement', '')
    if type_filter:
        paiements = paiements.filter(type_paiement=type_filter)
    
    # Pagination
    paginator = Paginator(paiements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': paiements.count(),
        'valides': paiements.filter(statut='valide').count(),
        'en_attente': paiements.filter(statut='en_attente').count(),
        'refuses': paiements.filter(statut='refuse').count(),
        'montant_total': paiements.aggregate(total=Sum('montant'))['total'] or 0,
    }
    
    context = {
        'page_obj': page_obj,
        'paiements': page_obj,
        'stats': stats,
        'query': query,
        'statut_filter': statut_filter,
        'type_filter': type_filter,
        'locataire_id': locataire_id,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'label': 'Paiements'}
        ]
    }
    
    # Ajouter les informations du locataire si filtré
    if locataire_obj:
        context['locataire'] = locataire_obj
        context['breadcrumbs'].append({'label': f'Historique - {locataire_obj.get_nom_complet()}'})
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_dashboard(request)
    
    return render(request, 'paiements/liste_paiements.html', context)
