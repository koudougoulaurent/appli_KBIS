from django.shortcuts import render
from django.db.models import Sum, Q, F, DecimalField, Count
from paiements.models import Paiement, RecapMensuel
from contrats.models import Contrat
from proprietes.models import Bailleur
from proprietes.models import ChargesBailleur
from datetime import date, datetime, timedelta
from decimal import Decimal
import csv
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io


def statistiques_globales(request):
    # Détermination de la période (mois/année)
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))
    
    # Calcul mois précédent pour comparaison
    if mois == 1:
        mois_precedent = 12
        annee_precedent = annee - 1
    else:
        mois_precedent = mois - 1
        annee_precedent = annee
    
    # Calcul mois suivant pour navigation
    if mois == 12:
        mois_suivant = 1
        annee_suivant = annee + 1
    else:
        mois_suivant = mois + 1
        annee_suivant = annee

    # Date range pour le mois
    date_debut_mois = date(annee, mois, 1)
    if mois == 12:
        date_fin_mois = date(annee + 1, 1, 1) - timedelta(days=1)
    else:
        date_fin_mois = date(annee, mois + 1, 1) - timedelta(days=1)
    
    # Contrats actifs avec loyers attendus pour le mois
    contrats_actifs = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False,
        date_debut__lte=date_fin_mois
    ).filter(
        Q(date_fin__gte=date_debut_mois) | Q(date_fin__isnull=True)
    ).select_related('locataire', 'propriete')
    
    nombre_contrats_actifs = contrats_actifs.count()
    
    # Total loyers attendus (somme des loyers de tous les contrats actifs)
    total_loyers_attendus = sum(
        (contrat.loyer_mensuel or Decimal('0')) for contrat in contrats_actifs
    )

    # MONTANT PAYÉ ce mois = paiements réellement confirmés durant ce mois
    paiements_mois = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='valide'
    )
    total_paye = paiements_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    # RECETTES TOTALES = TOTAL RÉELLEMENT ENCAISSÉ ce mois (même valeur que montant payé)
    # C'est le montant critique pour la production : ce qui entre réellement en caisse
    total_recettes = total_paye
    
    # RECETTES ENCAISSÉES PAR JOUR - Compatible SQLite et PostgreSQL
    from collections import defaultdict
    recettes_dict = defaultdict(lambda: {'total': Decimal('0'), 'nombre_paiements': 0})
    
    for paiement in paiements_mois:
        jour = paiement.date_paiement.date() if hasattr(paiement.date_paiement, 'date') else paiement.date_paiement
        recettes_dict[jour]['total'] += paiement.montant
        recettes_dict[jour]['nombre_paiements'] += 1
    
    # Convertir en liste triée
    recettes_par_jour = [
        {'jour': jour, 'total': data['total'], 'nombre_paiements': data['nombre_paiements']}
        for jour, data in sorted(recettes_dict.items())
    ]

    # Contrats en retard (échéance dépassée, paiement non reçu pour le mois actuel)
    # Récupérer les IDs des contrats qui ONT payé ce mois
    contrats_avec_paiement_ids = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='valide',
        contrat__isnull=False
    ).values_list('contrat_id', flat=True).distinct()
    
    # Contrats actifs SANS paiement = en retard (limité à 50 pour éviter surcharge mémoire)
    contrats_retard = contrats_actifs.exclude(
        id__in=contrats_avec_paiement_ids
    )[:50]

    # CALCUL PAR BAILLEUR : total dû et commissions (OPTIMISÉ)
    # Utiliser prefetch pour éviter N+1 queries
    from django.db.models import Prefetch
    
    # Calculer directement avec annotation au lieu de boucler
    total_du_bailleurs = Decimal('0')
    total_commissions = Decimal('0')
    
    # Somme de tous les loyers des contrats actifs
    for contrat in contrats_actifs:
        loyer = contrat.loyer_mensuel or Decimal('0')
        commission = (loyer * Decimal('0.10')).quantize(Decimal('0.01'))
        total_commissions += commission
        total_du_bailleurs += (loyer - commission)

    # Total charges bailleur du mois
    charges_mois = ChargesBailleur.objects.filter(
        date_charge__year=annee,
        date_charge__month=mois
    )
    total_charges_bailleur = charges_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')

    # Compter le nombre total de contrats en retard (avant la limite de 50)
    nombre_contrats_retard = contrats_actifs.exclude(
        id__in=contrats_avec_paiement_ids
    ).count()
    
    # CALCUL DES STATISTIQUES DU MOIS PRÉCÉDENT pour comparaison
    paiements_mois_precedent = Paiement.objects.filter(
        date_paiement__year=annee_precedent,
        date_paiement__month=mois_precedent,
        statut='valide'
    )
    total_paye_mois_precedent = paiements_mois_precedent.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    # CALCUL DES INDICATEURS DE PERFORMANCE
    # Taux de recouvrement = (recettes encaissées / loyers attendus) * 100
    if total_loyers_attendus > 0:
        taux_recouvrement = (total_recettes / total_loyers_attendus * 100).quantize(Decimal('0.01'))
    else:
        taux_recouvrement = Decimal('0')
    
    # Evolution vs mois précédent
    if total_paye_mois_precedent > 0:
        evolution_pourcent = ((total_recettes - total_paye_mois_precedent) / total_paye_mois_precedent * 100).quantize(Decimal('0.01'))
    else:
        evolution_pourcent = Decimal('0') if total_recettes == 0 else Decimal('100')
    
    evolution_montant = total_recettes - total_paye_mois_precedent

    context = {
        'mois': mois,
        'annee': annee,
        'mois_precedent': mois_precedent,
        'annee_precedent': annee_precedent,
        'mois_suivant': mois_suivant,
        'annee_suivant': annee_suivant,
        'total_recettes': total_recettes,
        'total_paye': total_paye,
        'nombre_contrats_actifs': nombre_contrats_actifs,
        'total_loyers_attendus': total_loyers_attendus,
        'contrats_retard': contrats_retard,
        'nombre_contrats_retard': nombre_contrats_retard,
        'total_du_bailleurs': total_du_bailleurs,
        'total_commissions': total_commissions,
        'total_charges_bailleur': total_charges_bailleur,
        'recettes_par_jour': recettes_par_jour,
        # Nouveaux indicateurs
        'taux_recouvrement': taux_recouvrement,
        'evolution_pourcent': evolution_pourcent,
        'evolution_montant': evolution_montant,
        'total_paye_mois_precedent': total_paye_mois_precedent,
    }
    return render(request, 'statistiques/statistiques_globales.html', context)


def export_statistiques_csv(request):
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))
    
    # Date range pour le mois
    date_debut_mois = date(annee, mois, 1)
    if mois == 12:
        date_fin_mois = date(annee + 1, 1, 1) - timedelta(days=1)
    else:
        date_fin_mois = date(annee, mois + 1, 1) - timedelta(days=1)
    
    # Contrats actifs
    contrats_actifs = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False,
        date_debut__lte=date_fin_mois
    ).filter(
        Q(date_fin__gte=date_debut_mois) | Q(date_fin__isnull=True)
    ).select_related('locataire', 'propriete')
    
    nombre_contrats_actifs = contrats_actifs.count()
    
    # Total loyers attendus
    total_loyers_attendus = sum(
        (contrat.loyer_mensuel or Decimal('0')) for contrat in contrats_actifs
    )
    
    # Montant payé ce mois
    paiements_mois = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='valide'
    )
    total_paye = paiements_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    # RECETTES TOTALES = TOTAL RÉELLEMENT ENCAISSÉ ce mois (même valeur que montant payé)
    total_recettes = total_paye
    
    # RECETTES ENCAISSÉES PAR JOUR - Compatible SQLite et PostgreSQL
    from collections import defaultdict
    recettes_dict = defaultdict(lambda: {'total': Decimal('0'), 'nombre_paiements': 0})
    
    for paiement in paiements_mois:
        jour = paiement.date_paiement.date() if hasattr(paiement.date_paiement, 'date') else paiement.date_paiement
        recettes_dict[jour]['total'] += paiement.montant
        recettes_dict[jour]['nombre_paiements'] += 1
    
    # Convertir en liste triée
    recettes_par_jour = [
        {'jour': jour, 'total': data['total'], 'nombre_paiements': data['nombre_paiements']}
        for jour, data in sorted(recettes_dict.items())
    ]
    
    # Contrats en retard
    contrats_avec_paiement_ids = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='valide',
        contrat__isnull=False
    ).values_list('contrat_id', flat=True).distinct()
    
    contrats_retard = contrats_actifs.exclude(id__in=contrats_avec_paiement_ids)
    
    # Calcul par bailleur
    bailleurs = Bailleur.objects.all()
    total_du_bailleurs = Decimal('0')
    total_commissions = Decimal('0')
    
    for bailleur in bailleurs:
        contrats_bailleur = contrats_actifs.filter(propriete__bailleur=bailleur)
        loyers_bailleur = sum(
            (contrat.loyer_mensuel or Decimal('0')) for contrat in contrats_bailleur
        )
        commission_bailleur = (loyers_bailleur * Decimal('0.10')).quantize(Decimal('0.01'))
        montant_du_bailleur = loyers_bailleur - commission_bailleur
        total_du_bailleurs += montant_du_bailleur
        total_commissions += commission_bailleur
    
    # Total charges bailleur
    charges_mois = ChargesBailleur.objects.filter(
        date_charge__year=annee,
        date_charge__month=mois
    )
    total_charges_bailleur = charges_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="statistiques_{mois}_{annee}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Statistique', 'Valeur'])
    writer.writerow(['Mois', mois])
    writer.writerow(['Année', annee])
    writer.writerow(['Nombre de contrats actifs', nombre_contrats_actifs])
    writer.writerow(['Total loyers attendus', total_loyers_attendus])
    writer.writerow(['Recettes totales', total_recettes])
    writer.writerow(['Montant payé ce mois', total_paye])
    writer.writerow(['Total dû aux bailleurs', total_du_bailleurs])
    writer.writerow(['Total commissions agence', total_commissions])
    writer.writerow(['Total charges bailleur', total_charges_bailleur])
    writer.writerow([])
    writer.writerow(['RECETTES ENCAISSÉES PAR JOUR'])
    writer.writerow(['Date', 'Montant', 'Nombre de paiements'])
    for recette in recettes_par_jour:
        writer.writerow([recette['jour'].strftime('%d/%m/%Y'), recette['total'], recette['nombre_paiements']])
    writer.writerow([])
    writer.writerow(['Contrats en retard', contrats_retard.count()])
    for contrat in contrats_retard[:100]:  # Limité à 100 pour CSV
        writer.writerow([str(contrat)])
    return response


def export_statistiques_pdf(request):
    """Export des statistiques globales en PDF"""
    today = date.today()
    now = datetime.now()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))
    
    # Date range pour le mois
    date_debut_mois = date(annee, mois, 1)
    if mois == 12:
        date_fin_mois = date(annee + 1, 1, 1) - timedelta(days=1)
    else:
        date_fin_mois = date(annee, mois + 1, 1) - timedelta(days=1)
    
    # Contrats actifs
    contrats_actifs = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False,
        date_debut__lte=date_fin_mois
    ).filter(
        Q(date_fin__gte=date_debut_mois) | Q(date_fin__isnull=True)
    ).select_related('locataire', 'propriete')
    
    nombre_contrats_actifs = contrats_actifs.count()
    
    # Total loyers attendus
    total_loyers_attendus = sum(
        (contrat.loyer_mensuel or Decimal('0')) for contrat in contrats_actifs
    )
    
    # Montant payé ce mois
    paiements_mois = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='valide'
    )
    total_paye = paiements_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    # RECETTES TOTALES = TOTAL RÉELLEMENT ENCAISSÉ ce mois (même valeur que montant payé)
    total_recettes = total_paye
    
    # RECETTES ENCAISSÉES PAR JOUR - Compatible SQLite et PostgreSQL
    from collections import defaultdict
    recettes_dict = defaultdict(lambda: {'total': Decimal('0'), 'nombre_paiements': 0})
    
    for paiement in paiements_mois:
        jour = paiement.date_paiement.date() if hasattr(paiement.date_paiement, 'date') else paiement.date_paiement
        recettes_dict[jour]['total'] += paiement.montant
        recettes_dict[jour]['nombre_paiements'] += 1
    
    # Convertir en liste triée
    recettes_par_jour = [
        {'jour': jour, 'total': data['total'], 'nombre_paiements': data['nombre_paiements']}
        for jour, data in sorted(recettes_dict.items())
    ]
    
    # Contrats en retard
    contrats_avec_paiement_ids = Paiement.objects.filter(
        date_paiement__year=annee,
        date_paiement__month=mois,
        statut='valide',
        contrat__isnull=False
    ).values_list('contrat_id', flat=True).distinct()
    
    contrats_retard = contrats_actifs.exclude(id__in=contrats_avec_paiement_ids)[:50]
    nombre_contrats_retard = contrats_actifs.exclude(id__in=contrats_avec_paiement_ids).count()
    
    # Calcul par bailleur
    bailleurs = Bailleur.objects.all()
    total_du_bailleurs = Decimal('0')
    total_commissions = Decimal('0')
    
    for bailleur in bailleurs:
        contrats_bailleur = contrats_actifs.filter(propriete__bailleur=bailleur)
        loyers_bailleur = sum(
            (contrat.loyer_mensuel or Decimal('0')) for contrat in contrats_bailleur
        )
        commission_bailleur = (loyers_bailleur * Decimal('0.10')).quantize(Decimal('0.01'))
        montant_du_bailleur = loyers_bailleur - commission_bailleur
        total_du_bailleurs += montant_du_bailleur
        total_commissions += commission_bailleur
    
    # Total charges bailleur
    charges_mois = ChargesBailleur.objects.filter(
        date_charge__year=annee,
        date_charge__month=mois
    )
    total_charges_bailleur = charges_mois.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    
    # Préparer le contexte pour le template PDF
    context = {
        'mois': mois,
        'annee': annee,
        'date_generation': now,
        'nombre_contrats_actifs': nombre_contrats_actifs,
        'total_loyers_attendus': total_loyers_attendus,
        'total_recettes': total_recettes,
        'total_paye': total_paye,
        'total_du_bailleurs': total_du_bailleurs,
        'total_commissions': total_commissions,
        'total_charges_bailleur': total_charges_bailleur,
        'contrats_retard': contrats_retard,
        'nombre_contrats_retard': nombre_contrats_retard,
        'recettes_par_jour': recettes_par_jour,
    }
    
    # Générer le HTML à partir du template
    html_string = render_to_string('statistiques/statistiques_pdf.html', context)
    
    # Créer la réponse HTTP avec PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statistiques_{mois}_{annee}.pdf"'
    
    # Générer le PDF avec xhtml2pdf
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    
    pdf_buffer.seek(0)
    response.write(pdf_buffer.getvalue())
    pdf_buffer.close()
    
    return response


