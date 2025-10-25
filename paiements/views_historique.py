"""
Vues pour l'historique des paiements par contrat/locataire
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from paiements.models import Paiement
from contrats.models import Contrat
from core.utils import check_group_permissions


@login_required
def historique_paiements_contrat(request, contrat_id):
    """
    Vue corrigée pour afficher l'historique des paiements d'un contrat
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, [], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    try:
        contrat = get_object_or_404(Contrat, id=contrat_id)
    except Exception:
        messages.error(request, 'Contrat non trouvé')
        return redirect('contrats:liste')
    
    # Récupérer tous les paiements du contrat
    paiements = Paiement.objects.filter(
        contrat=contrat,
        is_deleted=False
    ).order_by('-date_paiement', '-date_creation')
    
    # Créer une liste simple des paiements pour forcer l'affichage
    paiements_list = []
    for paiement in paiements:
        paiements_list.append({
            'id': paiement.id,
            'type_paiement': paiement.type_paiement,
            'montant': float(paiement.montant),
            'date_paiement': paiement.date_paiement.strftime('%d/%m/%Y'),
            'statut': paiement.statut,
            'reference': paiement.reference_paiement,
            'mois_paye': paiement.mois_paye,
            'mode_paiement': paiement.mode_paiement,
            'date_creation': paiement.date_creation,
            'notes': paiement.notes,
        })
    
    # Statistiques basées sur la liste simple
    stats = {
        'total_paiements': len(paiements_list),
        'total_montant': sum(p['montant'] for p in paiements_list),
        'paiements_valides': len([p for p in paiements_list if p['statut'] == 'valide']),
        'paiements_en_attente': len([p for p in paiements_list if p['statut'] == 'en_attente']),
        'paiements_refuses': len([p for p in paiements_list if p['statut'] == 'refuse']),
    }
    
    # Statistiques par type de paiement
    stats_par_type = {}
    for paiement in paiements_list:
        type_paiement = paiement['type_paiement']
        if type_paiement not in stats_par_type:
            stats_par_type[type_paiement] = {
                'display': paiement['type_paiement'].title(),
                'count': 0,
                'montant_total': 0
            }
        stats_par_type[type_paiement]['count'] += 1
        stats_par_type[type_paiement]['montant_total'] += paiement['montant']
    
    # Paiements récents (5 derniers)
    paiements_recents = paiements_list[:5]
    
    # Paiements par mois
    paiements_par_mois = defaultdict(lambda: {'paiements': [], 'montant_total': 0})
    for paiement in paiements_list:
        mois_cle = paiement['date_paiement'][:7]  # YYYY-MM
        paiements_par_mois[mois_cle]['paiements'].append(paiement)
        paiements_par_mois[mois_cle]['montant_total'] += paiement['montant']
    
    # Trier par mois
    paiements_par_mois = dict(sorted(paiements_par_mois.items(), reverse=True))
    
    # Debug pour vérifier
    print(f"=== DEBUG CONTRAT {contrat_id} ===")
    print(f"Paiements trouvés: {len(paiements_list)}")
    print(f"Contrat: {contrat.numero_contrat}")
    print(f"Locataire: {contrat.locataire.get_nom_complet()}")
    print(f"Propriété: {contrat.propriete.titre}")
    for p in paiements_list:
        print(f"- {p['type_paiement']}: {p['montant']} F CFA ({p['date_paiement']})")
    
    context = {
        'contrat': contrat,
        'locataire': contrat.locataire,
        'propriete': contrat.propriete,
        'paiements': paiements,
        'paiements_list': paiements_list,  # Liste simple pour forcer l'affichage
        'stats': stats,
        'stats_par_type': stats_par_type,
        'paiements_recents': paiements_recents,
        'paiements_par_mois': paiements_par_mois,
        'page_title': f'Historique des Paiements - {contrat.numero_contrat}',
        'generation_date': timezone.now(),
        'debug_info': {
            'paiements_count': len(paiements_list),
            'paiements_list': paiements_list,
            'contrat_info': {
                'numero': contrat.numero_contrat,
                'loyer': contrat.loyer_mensuel,
                'date_debut': contrat.date_debut,
            }
        }
    }
    
    return render(request, 'paiements/historique_paiements_contrat.html', context)


@login_required
def historique_paiements_contrat_old(request, contrat_id):
    """
    Affiche l'historique complet des paiements pour un contrat
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, [], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    try:
        contrat = get_object_or_404(Contrat, id=contrat_id)
    except Exception:
        messages.error(request, 'Contrat non trouvé')
        return redirect('contrats:liste')
    
    # Récupérer tous les paiements du contrat
    paiements = Paiement.objects.filter(
        contrat=contrat,
        is_deleted=False
    ).order_by('-date_paiement', '-date_creation')
    
    # Statistiques des paiements
    stats = {
        'total_paiements': paiements.count(),
        'total_montant': paiements.aggregate(Sum('montant'))['montant__sum'] or Decimal('0'),
        'paiements_valides': paiements.filter(statut='valide').count(),
        'paiements_en_attente': paiements.filter(statut='en_attente').count(),
        'paiements_refuses': paiements.filter(statut='refuse').count(),
    }
    
    # Statistiques par type de paiement
    stats_par_type = {}
    for type_paiement, display in Paiement.TYPE_PAIEMENT_CHOICES:
        paiements_type = paiements.filter(type_paiement=type_paiement)
        if paiements_type.exists():
            stats_par_type[type_paiement] = {
                'display': display,
                'count': paiements_type.count(),
                'montant_total': paiements_type.aggregate(Sum('montant'))['montant__sum'] or Decimal('0'),
                'dernier_paiement': paiements_type.first()
            }
    
    # Paiements récents (30 derniers jours)
    date_limite = timezone.now().date() - timedelta(days=30)
    paiements_recents = paiements.filter(date_paiement__gte=date_limite)
    
    # Paiements par mois (pour le graphique)
    paiements_par_mois = {}
    for paiement in paiements.filter(statut='valide'):
        mois_cle = paiement.date_paiement.replace(day=1)
        if mois_cle not in paiements_par_mois:
            paiements_par_mois[mois_cle] = {
                'mois': mois_cle,
                'paiements': [],
                'montant_total': Decimal('0')
            }
        paiements_par_mois[mois_cle]['paiements'].append(paiement)
        paiements_par_mois[mois_cle]['montant_total'] += paiement.montant
    
    # Trier par mois
    paiements_par_mois = dict(sorted(paiements_par_mois.items(), reverse=True))
    
    # Debug: Afficher les informations pour le développement
    print(f"DEBUG - Contrat: {contrat.numero_contrat}")
    print(f"DEBUG - Nombre de paiements: {paiements.count()}")
    print(f"DEBUG - Paiements: {list(paiements.values('type_paiement', 'montant', 'date_paiement'))}")
    print(f"DEBUG - Stats: {stats}")
    print(f"DEBUG - Stats par type: {stats_par_type}")
    print(f"DEBUG - Paiements QuerySet: {paiements}")
    print(f"DEBUG - Paiements SQL: {paiements.query}")
    
    # Créer une liste simple des paiements pour forcer l'affichage
    paiements_list = []
    for paiement in paiements:
        paiements_list.append({
            'id': paiement.id,
            'type_paiement': paiement.type_paiement,
            'montant': float(paiement.montant),
            'date_paiement': paiement.date_paiement.strftime('%d/%m/%Y'),
            'statut': paiement.statut,
            'reference': paiement.reference_paiement,
            'mois_paye': paiement.mois_paye,
            'mode_paiement': paiement.mode_paiement,
            'date_creation': paiement.date_creation,
            'notes': paiement.notes,
        })
    
    # Debug supplémentaire pour le contrat ID 12
    print(f"DEBUG CONTRAT {contrat_id}:")
    print(f"- Paiements QuerySet: {paiements.count()}")
    print(f"- Paiements List: {len(paiements_list)}")
    print(f"- Contrat: {contrat.numero_contrat}")
    print(f"- Locataire: {contrat.locataire.get_nom_complet()}")
    print(f"- Propriété: {contrat.propriete.titre}")
    print(f"- Loyer: {contrat.loyer_mensuel}")
    
    context = {
        'contrat': contrat,
        'locataire': contrat.locataire,
        'propriete': contrat.propriete,
        'paiements': paiements,
        'paiements_list': paiements_list,  # Liste simple pour forcer l'affichage
        'stats': stats,
        'stats_par_type': stats_par_type,
        'paiements_recents': paiements_recents,
        'paiements_par_mois': paiements_par_mois,
        'page_title': f'Historique des Paiements - {contrat.numero_contrat}',
        'generation_date': timezone.now(),
        'debug_info': {
            'paiements_count': paiements.count(),
            'paiements_list': list(paiements.values('type_paiement', 'montant', 'date_paiement', 'statut')),
            'contrat_info': {
                'numero': contrat.numero_contrat,
                'loyer': contrat.loyer_mensuel,
                'date_debut': contrat.date_debut,
            }
        }
    }
    
    return render(request, 'paiements/historique_paiements_contrat.html', context)


@login_required
def historique_paiements_contrat_imprimer(request, contrat_id):
    """
    Version imprimable de l'historique des paiements
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, [], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    try:
        contrat = get_object_or_404(Contrat, id=contrat_id)
    except Exception:
        messages.error(request, 'Contrat non trouvé')
        return redirect('contrats:liste')
    
    # Récupérer tous les paiements du contrat
    paiements = Paiement.objects.filter(
        contrat=contrat,
        is_deleted=False
    ).order_by('-date_paiement', '-date_creation')
    
    # Statistiques des paiements
    stats = {
        'total_paiements': paiements.count(),
        'total_montant': paiements.aggregate(Sum('montant'))['montant__sum'] or Decimal('0'),
        'paiements_valides': paiements.filter(statut='valide').count(),
        'paiements_en_attente': paiements.filter(statut='en_attente').count(),
        'paiements_refuses': paiements.filter(statut='refuse').count(),
    }
    
    # Statistiques par type de paiement
    stats_par_type = {}
    for type_paiement, display in Paiement.TYPE_PAIEMENT_CHOICES:
        paiements_type = paiements.filter(type_paiement=type_paiement)
        if paiements_type.exists():
            stats_par_type[type_paiement] = {
                'display': display,
                'count': paiements_type.count(),
                'montant_total': paiements_type.aggregate(Sum('montant'))['montant__sum'] or Decimal('0'),
            }
    
    # Paiements par mois
    paiements_par_mois = {}
    for paiement in paiements.filter(statut='valide'):
        mois_cle = paiement.date_paiement.replace(day=1)
        if mois_cle not in paiements_par_mois:
            paiements_par_mois[mois_cle] = {
                'mois': mois_cle,
                'paiements': [],
                'montant_total': Decimal('0')
            }
        paiements_par_mois[mois_cle]['paiements'].append(paiement)
        paiements_par_mois[mois_cle]['montant_total'] += paiement.montant
    
    # Trier par mois
    paiements_par_mois = dict(sorted(paiements_par_mois.items(), reverse=True))
    
    context = {
        'contrat': contrat,
        'locataire': contrat.locataire,
        'propriete': contrat.propriete,
        'paiements': paiements,
        'stats': stats,
        'stats_par_type': stats_par_type,
        'paiements_par_mois': paiements_par_mois,
        'page_title': f'Historique des Paiements - {contrat.numero_contrat}',
        'generation_date': timezone.now(),
        'is_printable': True,
    }
    
    return render(request, 'paiements/historique_paiements_contrat_imprimer.html', context)


@login_required
@require_http_methods(["GET"])
def historique_paiements_ajax(request, contrat_id):
    """
    API AJAX pour récupérer l'historique des paiements
    """
    try:
        contrat = get_object_or_404(Contrat, id=contrat_id)
        
        # Filtres optionnels
        type_paiement = request.GET.get('type_paiement', '')
        statut = request.GET.get('statut', '')
        date_debut = request.GET.get('date_debut', '')
        date_fin = request.GET.get('date_fin', '')
        
        # Construire la requête
        paiements = Paiement.objects.filter(
            contrat=contrat,
            is_deleted=False
        )
        
        if type_paiement:
            paiements = paiements.filter(type_paiement=type_paiement)
        
        if statut:
            paiements = paiements.filter(statut=statut)
        
        if date_debut:
            paiements = paiements.filter(date_paiement__gte=date_debut)
        
        if date_fin:
            paiements = paiements.filter(date_paiement__lte=date_fin)
        
        paiements = paiements.order_by('-date_paiement', '-date_creation')
        
        # Préparer les données pour JSON
        paiements_data = []
        for paiement in paiements:
            paiements_data.append({
                'id': paiement.id,
                'reference': paiement.reference_paiement,
                'type_paiement': paiement.get_type_paiement_display(),
                'montant': float(paiement.montant),
                'date_paiement': paiement.date_paiement.strftime('%d/%m/%Y'),
                'statut': paiement.get_statut_display(),
                'statut_color': paiement.get_statut_color(),
                'mode_paiement': paiement.get_mode_paiement_display(),
                'mois_paye': paiement.mois_paye or '',
                'date_creation': paiement.date_creation.strftime('%d/%m/%Y %H:%M'),
            })
        
        return JsonResponse({
            'success': True,
            'paiements': paiements_data,
            'total': paiements.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def historique_paiements_locataire(request, locataire_id):
    """
    Affiche l'historique des paiements pour un locataire (tous ses contrats)
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, [], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    try:
        from proprietes.models import Locataire
        locataire = get_object_or_404(Locataire, id=locataire_id)
    except Exception:
        messages.error(request, 'Locataire non trouvé')
        return redirect('contrats:liste')
    
    # Récupérer tous les contrats du locataire
    contrats = Contrat.objects.filter(
        locataire=locataire,
        is_deleted=False
    ).order_by('-date_creation')
    
    # Récupérer tous les paiements de tous les contrats
    paiements = Paiement.objects.filter(
        contrat__in=contrats,
        is_deleted=False
    ).order_by('-date_paiement', '-date_creation')
    
    # Statistiques globales
    stats = {
        'total_contrats': contrats.count(),
        'total_paiements': paiements.count(),
        'total_montant': paiements.aggregate(Sum('montant'))['montant__sum'] or Decimal('0'),
        'paiements_valides': paiements.filter(statut='valide').count(),
        'paiements_en_attente': paiements.filter(statut='en_attente').count(),
        'paiements_refuses': paiements.filter(statut='refuse').count(),
    }
    
    # Statistiques par contrat
    stats_par_contrat = {}
    for contrat in contrats:
        paiements_contrat = paiements.filter(contrat=contrat)
        if paiements_contrat.exists():
            stats_par_contrat[contrat.id] = {
                'contrat': contrat,
                'count': paiements_contrat.count(),
                'montant_total': paiements_contrat.aggregate(Sum('montant'))['montant__sum'] or Decimal('0'),
                'dernier_paiement': paiements_contrat.first()
            }
    
    context = {
        'locataire': locataire,
        'contrats': contrats,
        'paiements': paiements,
        'stats': stats,
        'stats_par_contrat': stats_par_contrat,
        'page_title': f'Historique des Paiements - {locataire.get_nom_complet()}',
        'generation_date': timezone.now(),
    }
    
    return render(request, 'paiements/historique_paiements_locataire.html', context)
