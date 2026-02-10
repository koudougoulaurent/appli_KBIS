from django.shortcuts import render
from django.db.models import Sum, Q, F, DecimalField, Count
from paiements.models import Paiement, RecapMensuel
from contrats.models import Contrat
from proprietes.models import Bailleur
from proprietes.models import ChargesBailleur
from datetime import date, timedelta
from decimal import Decimal
import csv
from django.http import HttpResponse


def statistiques_globales(request):
    # Détermination de la période (mois/année)
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))

    # Recettes totales (tous paiements confirmés du mois)
    paiements_mois = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='confirme'
    )
    total_recettes = paiements_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')

    # Montant payé ce mois-ci
    total_paye = total_recettes

    # Contrats actifs avec loyers attendus pour le mois
    date_debut_mois = date(annee, mois, 1)
    if mois == 12:
        date_fin_mois = date(annee + 1, 1, 1) - timedelta(days=1)
    else:
        date_fin_mois = date(annee, mois + 1, 1) - timedelta(days=1)
    
    contrats_actifs = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False,
        date_debut__lte=date_fin_mois
    ).filter(
        Q(date_fin__gte=date_debut_mois) | Q(date_fin__isnull=True)
    ).select_related('locataire', 'propriete', 'bailleur')
    
    nombre_contrats_actifs = contrats_actifs.count()
    total_loyers_attendus = sum(
        (contrat.loyer_mensuel or Decimal('0')) for contrat in contrats_actifs
    )

    # Contrats en retard (échéance dépassée, paiement non reçu pour le mois actuel)
    # Récupérer les IDs des contrats qui ONT payé ce mois
    contrats_avec_paiement_ids = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='confirme',
        contrat__isnull=False
    ).values_list('contrat_id', flat=True).distinct()
    
    # Contrats actifs SANS paiement = en retard (limité à 50 pour éviter surcharge mémoire)
    contrats_retard = contrats_actifs.exclude(
        id__in=contrats_avec_paiement_ids
    )[:50]

    # Total dû aux bailleurs (calculé à partir des récaps mensuels)
    recaps_mois = RecapMensuel.objects.filter(
        mois_recap__year=annee,
        mois_recap__month=mois,
        is_deleted=False
    )
    
    total_du_bailleurs = Decimal('0')
    total_commissions_recaps = Decimal('0')
    
    for recap in recaps_mois:
        # Calculer les totaux pour chaque recap
        totaux = recap.calculer_totaux_bailleur()
        montant_paye = totaux.get('montant_reellement_paye', Decimal('0'))
        commission = totaux.get('commission_agence', Decimal('0'))
        
        total_du_bailleurs += montant_paye
        total_commissions_recaps += commission

    # Total commissions agence (10% sur tous les paiements confirmés du mois)
    total_commissions = paiements_mois.aggregate(
        total=Sum(F('montant') * Decimal('0.10'), output_field=DecimalField())
    )['total'] or Decimal('0')

    # Total charges bailleur du mois
    charges_mois = ChargesBailleur.objects.filter(
        date_charge__year=annee,
        date_charge__month=mois
    )
    total_charges_bailleur = charges_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')

    # Compter le nombre total de contrats en retard (avant la limite de 50)
    nombre_contrats_retard = contrats_actifs.exclude(
        id__in=Paiement.objects.filter(
            date_paiement__year=annee,
            date_paiement__month=mois,
            statut='confirme',
            contrat__isnull=False
        ).values_list('contrat_id', flat=True).distinct()
    ).count()

    context = {
        'mois': mois,
        'annee': annee,
        'total_recettes': total_recettes,
        'total_paye': total_paye,
        'nombre_contrats_actifs': nombre_contrats_actifs,
        'total_loyers_attendus': total_loyers_attendus,
        'contrats_retard': contrats_retard,
        'nombre_contrats_retard': nombre_contrats_retard,
        'total_du_bailleurs': total_du_bailleurs,
        'total_commissions': total_commissions,
        'total_commissions_recaps': total_commissions_recaps,
        'total_charges_bailleur': total_charges_bailleur,
    }
    return render(request, 'statistiques/statistiques_globales.html', context)


def export_statistiques_csv(request):
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))
    paiements_mois = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='confirme'
    )
    total_recettes = paiements_mois.aggregate(total=Sum('montant'))['total'] or 0
    total_paye = total_recettes
    contrats = Contrat.objects.filter(est_actif=True, est_resilie=False)
    contrats_retard = []
    for contrat in contrats:
        dernier_paiement = Paiement.objects.filter(contrat=contrat, statut='confirme').order_by('-date_paiement').first()
        if dernier_paiement:
            if dernier_paiement.date_paiement.year < annee or (dernier_paiement.date_paiement.year == annee and dernier_paiement.date_paiement.month < mois):
                contrats_retard.append(contrat)
        else:
            contrats_retard.append(contrat)
    total_du_bailleurs = 0
    for bailleur in Bailleur.objects.all():
        if hasattr(bailleur, 'get_montant_du_pour_mois'):
            total_du_bailleurs += bailleur.get_montant_du_pour_mois(mois, annee)
    total_commissions = paiements_mois.aggregate(
        total=Sum(F('montant') * Decimal('0.10'), output_field=DecimalField())
    )['total'] or Decimal('0')
    charges_mois = ChargesBailleur.objects.filter(
        date_charge__year=annee,
        date_charge__month=mois
    )
    total_charges_bailleur = charges_mois.aggregate(total=Sum('montant'))['total'] or 0
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="statistiques_{mois}_{annee}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Statistique', 'Valeur'])
    writer.writerow(['Mois', mois])
    writer.writerow(['Année', annee])
    writer.writerow(['Recettes totales', total_recettes])
    writer.writerow(['Montant payé', total_paye])
    writer.writerow(['Total dû aux bailleurs', total_du_bailleurs])
    writer.writerow(['Total commissions agence', total_commissions])
    writer.writerow(['Total charges bailleur', total_charges_bailleur])
    writer.writerow([])
    writer.writerow(['Contrats en retard'])
    for contrat in contrats_retard:
        writer.writerow([str(contrat)])
    return response
