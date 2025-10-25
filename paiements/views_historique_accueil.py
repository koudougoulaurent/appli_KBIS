"""
Vue d'accueil pour l'historique des paiements
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from paiements.models import Paiement
from contrats.models import Contrat
from proprietes.models import Locataire
from core.utils import check_group_permissions


@login_required
def accueil_historique_paiements(request):
    """
    Page d'accueil pour l'historique des paiements avec statistiques globales
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, [], 'view')
    if not permissions['allowed']:
        return render(request, 'paiements/accueil_historique_paiements.html', {
            'error': permissions['message']
        })
    
    # Statistiques globales
    stats_globales = {
        'total_paiements': Paiement.objects.filter(is_deleted=False).count(),
        'total_montant': Paiement.objects.filter(is_deleted=False).aggregate(Sum('montant'))['montant__sum'] or 0,
        'paiements_valides': Paiement.objects.filter(is_deleted=False, statut='valide').count(),
        'paiements_en_attente': Paiement.objects.filter(is_deleted=False, statut='en_attente').count(),
        'paiements_refuses': Paiement.objects.filter(is_deleted=False, statut='refuse').count(),
    }
    
    # Statistiques par type de paiement
    stats_par_type = {}
    for type_paiement, display in Paiement.TYPE_PAIEMENT_CHOICES:
        paiements_type = Paiement.objects.filter(
            is_deleted=False,
            type_paiement=type_paiement
        )
        if paiements_type.exists():
            stats_par_type[type_paiement] = {
                'display': display,
                'count': paiements_type.count(),
                'montant_total': paiements_type.aggregate(Sum('montant'))['montant__sum'] or 0,
            }
    
    # Paiements récents (7 derniers jours)
    date_limite = timezone.now().date() - timedelta(days=7)
    paiements_recents = Paiement.objects.filter(
        is_deleted=False,
        date_paiement__gte=date_limite
    ).order_by('-date_paiement')[:10]
    
    # Contrats avec le plus de paiements
    contrats_actifs = Contrat.objects.filter(
        is_deleted=False,
        est_actif=True
    ).annotate(
        nb_paiements=Count('paiements', filter=Q(paiements__is_deleted=False))
    ).order_by('-nb_paiements')[:5]
    
    # Locataires avec le plus de paiements
    locataires_actifs = Locataire.objects.filter(
        is_deleted=False
    ).annotate(
        nb_paiements=Count('contrats__paiements', filter=Q(contrats__paiements__is_deleted=False))
    ).order_by('-nb_paiements')[:5]
    
    # Paiements par mois (6 derniers mois)
    paiements_par_mois = []
    for i in range(6):
        mois_date = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        paiements_mois = Paiement.objects.filter(
            is_deleted=False,
            date_paiement__year=mois_date.year,
            date_paiement__month=mois_date.month
        )
        
        paiements_par_mois.append({
            'mois': mois_date,
            'count': paiements_mois.count(),
            'montant': paiements_mois.aggregate(Sum('montant'))['montant__sum'] or 0,
        })
    
    # Préparer les données pour le JavaScript
    contrats_data = []
    for contrat in contrats_actifs:
        contrats_data.append({
            'id': contrat.id,
            'numero': contrat.numero_contrat,
            'locataire': contrat.locataire.get_nom_complet(),
            'propriete': f"{contrat.propriete.titre} - {contrat.propriete.adresse}",
            'paiements': contrat.nb_paiements,
            'loyer': float(contrat.loyer_mensuel),
            'url_detail': f"/contrats/detail/{contrat.id}/",
            'url_historique': f"/paiements/historique/contrat/{contrat.id}/"
        })
    
    locataires_data = []
    for locataire in locataires_actifs:
        # Trouver le dernier paiement
        dernier_paiement = Paiement.objects.filter(
            contrat__locataire=locataire,
            is_deleted=False
        ).order_by('-date_paiement').first()
        
        locataires_data.append({
            'id': locataire.id,
            'nom': locataire.get_nom_complet(),
            'contrats': locataire.nb_paiements,  # Utiliser nb_paiements comme proxy pour le nombre de contrats
            'paiements': locataire.nb_paiements,
            'dernier_paiement': dernier_paiement.date_paiement.strftime('%d %b %Y') if dernier_paiement else 'Aucun',
            'url_profil': f"/proprietes/locataires/{locataire.id}/",
            'url_historique': f"/paiements/historique/locataire/{locataire.id}/"
        })
    
    # Statistiques pour les contrats
    stats_contrats = {
        'total_contrats': Contrat.objects.filter(is_deleted=False).count(),
        'contrats_actifs': Contrat.objects.filter(is_deleted=False, est_actif=True).count(),
        'contrats_resilies': Contrat.objects.filter(is_deleted=False, est_resilie=True).count(),
        'revenus_totaux': Paiement.objects.filter(is_deleted=False, contrat__is_deleted=False).aggregate(Sum('montant'))['montant__sum'] or 0,
    }
    
    # Statistiques pour les locataires
    stats_locataires = {
        'total_locataires': Locataire.objects.filter(is_deleted=False).count(),
        'locataires_actifs': Locataire.objects.filter(is_deleted=False).count(),
        'moyenne_contrats': 1.0,  # Valeur par défaut
        'moyenne_paiements': round(sum(loc.nb_paiements for loc in locataires_actifs) / max(len(locataires_actifs), 1), 1),
    }

    context = {
        'stats_globales': stats_globales,
        'stats_par_type': stats_par_type,
        'paiements_recents': paiements_recents,
        'contrats_actifs': contrats_actifs,
        'locataires_actifs': locataires_actifs,
        'paiements_par_mois': paiements_par_mois,
        'page_title': 'Historique des Paiements - Accueil',
        'generation_date': timezone.now(),
        # Données pour le JavaScript
        'contrats_data': contrats_data,
        'locataires_data': locataires_data,
        'stats_contrats': stats_contrats,
        'stats_locataires': stats_locataires,
    }
    
    return render(request, 'paiements/accueil_historique_paiements.html', context)
