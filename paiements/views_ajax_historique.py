"""
Vues AJAX pour l'historique des paiements dynamique
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from contrats.models import Contrat
from proprietes.models import Locataire
from paiements.models import Paiement


@login_required
@require_http_methods(["GET"])
def get_contrats_actifs_ajax(request):
    """Retourne les contrats les plus actifs en JSON"""
    try:
        # Vérification des permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, [], 'view')
        if not permissions['allowed']:
            return JsonResponse({
                'success': False,
                'error': 'Permissions insuffisantes'
            })
        # Récupérer les contrats avec le plus de paiements
        contrats = Contrat.objects.filter(
            is_deleted=False,
            est_actif=True
        ).annotate(
            nb_paiements=Count('paiements', filter=Q(paiements__is_deleted=False))
        ).order_by('-nb_paiements')[:5]
        
        contrats_data = []
        for contrat in contrats:
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
        
        # Statistiques des contrats
        total_contrats = Contrat.objects.filter(is_deleted=False).count()
        contrats_actifs = Contrat.objects.filter(is_deleted=False, est_actif=True).count()
        contrats_resilies = Contrat.objects.filter(is_deleted=False, est_resilie=True).count()
        
        # Calculer les revenus totaux
        revenus_totaux = Paiement.objects.filter(
            is_deleted=False,
            statut='valide',
            type_paiement='loyer'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'contrats': contrats_data,
            'statistiques': {
                'total_contrats': total_contrats,
                'contrats_actifs': contrats_actifs,
                'contrats_resilies': contrats_resilies,
                'revenus_totaux': float(revenus_totaux)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def get_locataires_actifs_ajax(request):
    """Retourne les locataires les plus actifs en JSON"""
    try:
        # Vérification des permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, [], 'view')
        if not permissions['allowed']:
            return JsonResponse({
                'success': False,
                'error': 'Permissions insuffisantes'
            })
        # Récupérer les locataires avec le plus de paiements
        locataires = Locataire.objects.filter(
            is_deleted=False
        ).annotate(
            nb_paiements=Count('contrats__paiements', filter=Q(contrats__paiements__is_deleted=False)),
            nb_contrats=Count('contrats', filter=Q(contrats__is_deleted=False))
        ).order_by('-nb_paiements')[:5]
        
        locataires_data = []
        for locataire in locataires:
            # Récupérer le dernier paiement
            dernier_paiement = Paiement.objects.filter(
                contrat__locataire=locataire,
                is_deleted=False
            ).order_by('-date_paiement').first()
            
            locataires_data.append({
                'id': locataire.id,
                'nom': locataire.get_nom_complet(),
                'contrats': locataire.nb_contrats,
                'paiements': locataire.nb_paiements,
                'dernier_paiement': dernier_paiement.date_paiement.strftime('%d %b %Y') if dernier_paiement else 'Aucun',
                'url_profil': f"/proprietes/locataires/{locataire.id}/",
                'url_historique': f"/paiements/historique/locataire/{locataire.id}/"
            })
        
        # Statistiques des locataires
        total_locataires = Locataire.objects.filter(is_deleted=False).count()
        locataires_actifs = Locataire.objects.filter(
            is_deleted=False,
            contrats__is_deleted=False,
            contrats__est_actif=True
        ).distinct().count()
        
        # Moyennes
        if total_locataires > 0:
            moyenne_contrats = Locataire.objects.filter(
                is_deleted=False
            ).annotate(
                nb_contrats=Count('contrats', filter=Q(contrats__is_deleted=False))
            ).aggregate(moyenne=Sum('nb_contrats'))['moyenne'] or 0
            moyenne_contrats = moyenne_contrats / total_locataires if total_locataires > 0 else 0
            
            moyenne_paiements = Locataire.objects.filter(
                is_deleted=False
            ).annotate(
                nb_paiements=Count('contrats__paiements', filter=Q(contrats__paiements__is_deleted=False))
            ).aggregate(moyenne=Sum('nb_paiements'))['moyenne'] or 0
            moyenne_paiements = moyenne_paiements / total_locataires if total_locataires > 0 else 0
        else:
            moyenne_contrats = 0
            moyenne_paiements = 0
        
        return JsonResponse({
            'success': True,
            'locataires': locataires_data,
            'statistiques': {
                'total_locataires': total_locataires,
                'locataires_actifs': locataires_actifs,
                'moyenne_contrats': round(moyenne_contrats, 1),
                'moyenne_paiements': round(moyenne_paiements, 1)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
