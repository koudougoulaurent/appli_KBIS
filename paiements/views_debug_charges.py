"""
Vue de débogage temporaire pour vérifier les charges bailleur
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from paiements.models import RecapMensuel, ChargeBailleur
from decimal import Decimal


@login_required
def debug_charges_recap(request, recap_id):
    """
    Vue de débogage pour vérifier les charges bailleur d'un récapitulatif.
    URL: /paiements/debug-charges-recap/<recap_id>/
    """
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
        
        # Récupérer TOUTES les charges du bailleur pour ce mois (tous statuts)
        toutes_charges = ChargeBailleur.objects.filter(
            bailleur=recap.bailleur,
            date_charge__year=recap.mois_recap.year,
            date_charge__month=recap.mois_recap.month,
        )
        
        # Récupérer seulement les charges 'valide'
        charges_valides = ChargeBailleur.objects.filter(
            bailleur=recap.bailleur,
            date_charge__year=recap.mois_recap.year,
            date_charge__month=recap.mois_recap.month,
            statut__in=['valide']
        ).exclude(
            retrait_utilise__isnull=False
        )
        
        # Préparer les détails
        details_toutes = []
        total_toutes = Decimal('0')
        for charge in toutes_charges:
            montant = getattr(charge, 'montant_restant', None) or charge.montant
            details_toutes.append({
                'id': charge.id,
                'description': charge.description,
                'montant': float(montant),
                'statut': charge.statut,
                'date_charge': charge.date_charge.strftime('%Y-%m-%d'),
                'retrait_utilise': charge.retrait_utilise_id if hasattr(charge, 'retrait_utilise_id') else None,
            })
            total_toutes += montant
        
        details_valides = []
        total_valides = Decimal('0')
        for charge in charges_valides:
            montant = getattr(charge, 'montant_restant', None) or charge.montant
            details_valides.append({
                'id': charge.id,
                'description': charge.description,
                'montant': float(montant),
                'statut': charge.statut,
                'date_charge': charge.date_charge.strftime('%Y-%m-%d'),
            })
            total_valides += montant
        
        # Forcer le recalcul
        totaux_calcules = recap.calculer_totaux_bailleur()
        
        # Rafraîchir pour voir les valeurs sauvegardées
        recap.refresh_from_db()
        
        return JsonResponse({
            'recap_id': recap.id,
            'bailleur': recap.bailleur.nom if recap.bailleur else None,
            'mois_recap': recap.mois_recap.strftime('%Y-%m-%d'),
            'charges_existantes': {
                'toutes': {
                    'nombre': toutes_charges.count(),
                    'total': float(total_toutes),
                    'details': details_toutes,
                },
                'valides_filtre': {
                    'nombre': charges_valides.count(),
                    'total': float(total_valides),
                    'details': details_valides,
                },
            },
            'recap_valeurs_bdd': {
                'total_loyers_bruts': float(recap.total_loyers_bruts),
                'total_charges_bailleur': float(recap.total_charges_bailleur),
                'total_net_a_payer': float(recap.total_net_a_payer),
            },
            'totaux_calcules': {
                'total_loyers_bruts': float(totaux_calcules.get('total_loyers_bruts', 0)),
                'total_charges_bailleur': float(totaux_calcules.get('total_charges_bailleur', 0)),
                'total_net_a_payer': float(totaux_calcules.get('total_net_a_payer', 0)),
            },
        })
        
    except RecapMensuel.DoesNotExist:
        return JsonResponse({'error': 'Récapitulatif introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
