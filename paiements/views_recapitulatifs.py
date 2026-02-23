#!/usr/bin/env python3
"""
Vues pour la gestion des récapitulatifs mensuels
================================================

Ce module gère la création, validation et envoi des récapitulatifs mensuels
qui résument toutes les opérations financières pour chaque bailleur.
"""

import logging
from datetime import datetime as dt, date
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from django.urls import reverse

from .models import RecapMensuel
from .forms import RecapMensuelForm
from .services_recap_paiement import ServiceRecapPaiementMensuel
from proprietes.models import Bailleur

logger = logging.getLogger(__name__)


def _force_list_safe(data):
    """
    Force les données à être une liste Python standard.
    Gère les cas où data peut être un QuerySet, un NotImplementedType, ou autre.
    """
    if data is None:
        return []
    if isinstance(data, list):
        return data
    try:
        # Si c'est un QuerySet ou autre itérable, convertir en liste
        return list(data)
    except (TypeError, AttributeError):
        # Si la conversion échoue, retourner une liste vide
        logger.warning(f"Impossible de convertir {type(data)} en liste, retour d'une liste vide")
        return []


@login_required
def liste_recapitulatifs(request):
    """Liste de tous les récapitulatifs mensuels."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Vérifier si l'utilisateur est PRIVILEGE
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Filtres
    mois = request.GET.get('mois')
    statut = request.GET.get('statut')
    type_recap = request.GET.get('type')
    tri_par = request.GET.get('tri', 'mois')  # nom du champ à trier
    tri_sens = request.GET.get('sens', 'desc')  # 'asc' ou 'desc'
    recherche = request.GET.get('q', '').strip()
    
    # Récupérer uniquement les récapitulatifs non supprimés
    # Vérifier si les migrations sont appliquées en testant la présence des nouveaux champs
    from django.db import connection
    table_name = RecapMensuel._meta.db_table
    has_new_fields = False
    
    try:
        with connection.cursor() as cursor:
            # Vérifier si la colonne commission_agence existe
            if connection.vendor == 'sqlite':
                cursor.execute(f"""
                    SELECT name FROM pragma_table_info('{table_name}') WHERE name IN ('commission_agence', 'montant_reellement_paye')
                """)
            elif connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = %s AND column_name IN ('commission_agence', 'montant_reellement_paye')
                """, [table_name])
            else:
                # Pour MySQL
                cursor.execute("""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = %s AND COLUMN_NAME IN ('commission_agence', 'montant_reellement_paye')
                """, [table_name])
            has_new_fields = len(cursor.fetchall()) > 0
    except Exception:
        # En cas d'erreur, supposer que les champs n'existent pas
        has_new_fields = False
    

    # Récupérer les récapitulatifs
    if not has_new_fields:
        recapitulatifs = RecapMensuel.objects.filter(is_deleted=False).select_related('bailleur').defer('commission_agence', 'montant_reellement_paye')
    else:
        recapitulatifs = RecapMensuel.objects.filter(is_deleted=False).select_related('bailleur')

    # Appliquer les filtres
    if mois:
        try:
            from datetime import datetime
            date_mois = datetime.strptime(mois, '%Y-%m').date()
            recapitulatifs = recapitulatifs.filter(mois_recap__year=date_mois.year, mois_recap__month=date_mois.month)
        except (ValueError, TypeError):
            recapitulatifs = recapitulatifs.filter(mois_recap__icontains=mois)
    if statut:
        recapitulatifs = recapitulatifs.filter(statut=statut)

    # Recherche globale multi-champs intelligente
    if recherche:
        from django.db.models import Q
        # Recherche améliorée avec plus de champs
        recapitulatifs = recapitulatifs.filter(
            Q(bailleur__nom__icontains=recherche) |
            Q(bailleur__prenom__icontains=recherche) |
            Q(bailleur__numero_bailleur__icontains=recherche) |
            Q(mois_recap__icontains=recherche) |
            Q(statut__icontains=recherche) |
            Q(id__icontains=recherche)  # Recherche par ID
        )

    # Tri dynamique
    tri_map = {
        'mois': 'mois_recap',
        'statut': 'statut',
        'bailleur': 'bailleur__nom',
        'net': 'montant_net_a_payer',
        'loyers': 'total_loyers',
        'charges': 'total_charges',
    }
    tri_field = tri_map.get(tri_par, 'mois_recap')
    if tri_sens == 'asc':
        recapitulatifs = recapitulatifs.order_by(tri_field)
    else:
        recapitulatifs = recapitulatifs.order_by(f'-{tri_field}')
    
    # Grouper les récapitulatifs
    recaps_par_mois = {}
    recaps_par_statut = {}
    recaps_par_bailleur = {}
    
    for recap in recapitulatifs:
        mois_key = recap.mois_recap.strftime('%Y-%m')
        mois_label = recap.mois_recap.strftime('%B %Y')
        
        # Grouper par mois
        if mois_key not in recaps_par_mois:
            recaps_par_mois[mois_key] = {
                'label': mois_label,
                'recaps': []
            }
        recaps_par_mois[mois_key]['recaps'].append(recap)
        
        # Grouper par statut
        statut_key = recap.statut
        statut_label = recap.get_statut_display()
        if statut_key not in recaps_par_statut:
            recaps_par_statut[statut_key] = {
                'label': statut_label,
                'recaps': []
            }
        recaps_par_statut[statut_key]['recaps'].append(recap)
        
        # Grouper par bailleur
        if recap.bailleur:
            bailleur_key = recap.bailleur.id
            bailleur_label = recap.bailleur.get_nom_complet()
            if bailleur_key not in recaps_par_bailleur:
                recaps_par_bailleur[bailleur_key] = {
                    'label': bailleur_label,
                    'recaps': []
                }
            recaps_par_bailleur[bailleur_key]['recaps'].append(recap)
    
    # Pagination - on pagine le queryset complet
    paginator = Paginator(recapitulatifs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': recapitulatifs.count(),
        'brouillon': recapitulatifs.filter(statut='brouillon').count(),
        'valides': recapitulatifs.filter(statut='valide').count(),
        'envoyes': recapitulatifs.filter(statut='envoye').count(),
        'payes': recapitulatifs.filter(statut='paye').count(),
    }
    
    context = {
        'page_title': 'Récapitulatifs Mensuels',
        'page_icon': 'file-earmark-text',
        'page_obj': page_obj,
        'recaps_par_mois': recaps_par_mois,
        'recaps_par_statut': recaps_par_statut,
        'recaps_par_bailleur': recaps_par_bailleur,
        'tri_par': tri_par,
        'stats': stats,
        'is_privilege_user': is_privilege_user,
        'recherche': recherche,  # Variable pour la recherche intelligente
        'filtres': {
            'mois': mois,
            'statut': statut,
            'type_recap': type_recap
        }
    }
    
    return render(request, 'paiements/recapitulatifs/liste_recapitulatifs.html', context)


@login_required
def creer_recapitulatif(request):
    """Créer un nouveau récapitulatif mensuel."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recapitulatifs')
    
    if request.method == 'POST':
        form = RecapMensuelForm(request.POST)
        if form.is_valid():
            try:
                recapitulatif = form.save(commit=False)
                recapitulatif.cree_par = request.user
                # Set garanties_suffisantes to True by default to avoid database constraint error
                recapitulatif.garanties_suffisantes = True
                recapitulatif.save()
                
                messages.success(
                    request,
                    f"Récapitulatif créé avec succès pour {recapitulatif.mois_recap.strftime('%B %Y')}"
                )
                
                return redirect('paiements:dashboard')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création: {str(e)}")
                return render(request, 'paiements/recapitulatifs/creer_recapitulatif.html', {'form': form})
    else:
        form = RecapMensuelForm()
    
    context = {
        'page_title': 'Créer un Récapitulatif Mensuel',
        'page_icon': 'plus-circle',
        'form': form,
        'action': 'creer'
    }
    
    return render(request, 'paiements/recapitulatifs/creer_recapitulatif.html', context)


@login_required
def detail_recapitulatif(request, recapitulatif_id):
    """Détail d'un récapitulatif mensuel."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    recapitulatif = get_object_or_404(
        RecapMensuel.objects.select_related('bailleur'),
        pk=recapitulatif_id
    )
    
    # CRITIQUE : Recalculer TOUJOURS les totaux depuis la base de données pour garantir l'exactitude
    # Cela garantit que les calculs sont basés sur les données les plus récentes
    # et incluent toutes les propriétés louées du bailleur pour le mois concerné
    totaux_calcules = recapitulatif.calculer_totaux_bailleur()
    
    # Rafraîchir l'objet depuis la base de données pour récupérer les valeurs sauvegardées
    recapitulatif.refresh_from_db()
    
    # Utiliser les totaux calculés directement pour garantir l'exactitude
    # Si les totaux calculés sont valides, les utiliser, sinon utiliser les valeurs sauvegardées
    from decimal import Decimal
    
    if totaux_calcules and isinstance(totaux_calcules, dict):
        # Utiliser les valeurs calculées directement (plus récentes)
        totaux = {
            'total_loyers_bruts': totaux_calcules.get('total_loyers_bruts', recapitulatif.total_loyers_bruts),
            'total_charges_deductibles': totaux_calcules.get('total_charges_deductibles', recapitulatif.total_charges_deductibles),
            'total_charges_bailleur': totaux_calcules.get('total_charges_bailleur', recapitulatif.total_charges_bailleur or Decimal('0')),
            'total_net_a_payer': totaux_calcules.get('total_net_a_payer', recapitulatif.total_net_a_payer),
            'commission_agence': totaux_calcules.get('commission_agence', getattr(recapitulatif, 'commission_agence', None) or Decimal('0')),
            'montant_reellement_paye': totaux_calcules.get('montant_reellement_paye', getattr(recapitulatif, 'montant_reellement_paye', None) or Decimal('0')),
            'nombre_proprietes': totaux_calcules.get('nombre_proprietes', recapitulatif.nombre_proprietes),
            'nombre_contrats_actifs': totaux_calcules.get('nombre_contrats_actifs', recapitulatif.nombre_contrats_actifs),
            'nombre_paiements_recus': totaux_calcules.get('nombre_paiements_recus', recapitulatif.nombre_paiements_recus),
            'bailleur': recapitulatif.bailleur,  # Ajouter le bailleur pour le template
        }
    else:
        # Fallback : utiliser les valeurs sauvegardées si le calcul a échoué
        totaux = {
            'total_loyers_bruts': recapitulatif.total_loyers_bruts,
            'total_charges_deductibles': recapitulatif.total_charges_deductibles,
            'total_charges_bailleur': recapitulatif.total_charges_bailleur or Decimal('0'),
            'total_net_a_payer': recapitulatif.total_net_a_payer,
            'commission_agence': getattr(recapitulatif, 'commission_agence', None) or Decimal('0'),
            'montant_reellement_paye': getattr(recapitulatif, 'montant_reellement_paye', None) or Decimal('0'),
            'nombre_proprietes': recapitulatif.nombre_proprietes,
            'nombre_contrats_actifs': recapitulatif.nombre_contrats_actifs,
            'nombre_paiements_recus': recapitulatif.nombre_paiements_recus,
            'bailleur': recapitulatif.bailleur,
        }
    
    # CRITIQUE : Récupérer les détails des propriétés pour l'affichage dans le template
    # Cela garantit que toutes les propriétés louées sont affichées avec leurs informations correctes
    proprietes_details = recapitulatif.get_proprietes_details()
    
    # Ajouter les détails des propriétés aux totaux pour le template
    if totaux:
        totaux['details_proprietes'] = proprietes_details
    
    context = {
        'page_title': f'Récapitulatif - {recapitulatif.mois_recap.strftime("%B %Y")}',
        'page_icon': 'file-earmark-text',
        'recapitulatif': recapitulatif,
        'totaux': totaux,
        'proprietes_details': proprietes_details,  # Pour compatibilité avec d'autres templates
    }
    
    return render(request, 'paiements/recapitulatifs/detail_recapitulatif.html', context)


@login_required
def generer_recapitulatif_kbis(request, recapitulatif_id):
    """Génère un récapitulatif A4 paysage avec en-tête KBIS et pied de page dynamique.
    
    OPTIMISATIONS:
    - Requêtes DB optimisées avec select_related et prefetch_related
    - Préchargement des paiements pour le filtre de caution/avance
    """
    
    # Vérification des permissions
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    # Vérifier que le bailleur existe
    if not recapitulatif.bailleur:
        messages.error(request, 'Ce récapitulatif n\'a pas de bailleur associé. Impossible de générer le PDF.')
        return redirect('paiements:detail_recapitulatif', recapitulatif_id=recapitulatif_id)
    
    # Calculer les totaux
    totaux = recapitulatif.calculer_totaux_bailleur()
    
    # OPTIMISATION: Récupérer les propriétés avec tous les related objects préchargés
    from django.db.models import Prefetch
    from contrats.models import Contrat
    from paiements.models import Paiement
    
    # Précharger les paiements de type caution/avance validés pour le filtre
    paiements_caution_prefetch = Prefetch(
        'paiements',
        queryset=Paiement.objects.filter(
            type_paiement__in=['caution', 'avance'],
            statut='valide'
        ),
        to_attr='paiements_caution_avance'
    )
    
    contrats_prefetch = Prefetch(
        'contrats',
        queryset=Contrat.objects.filter(
            est_actif=True,
            est_resilie=False
        ).select_related('locataire').prefetch_related(paiements_caution_prefetch)
    )
    
    proprietes = recapitulatif.bailleur.proprietes.filter(
        is_deleted=False,
        contrats__est_actif=True,
        contrats__est_resilie=False
    ).distinct().select_related(
        'type_bien',
        'bailleur'
    ).prefetch_related(
        'unites_locatives',
        contrats_prefetch
    )
    
    # Préparer les données pour le récapitulatif
    proprietes_avec_details = []
    for propriete in proprietes:
        unites_locatives = propriete.unites_locatives.filter(is_deleted=False)
        
        # Calculer les totaux pour cette propriété
        loyer_total = propriete.get_loyer_actuel_calcule()
        
        proprietes_avec_details.append({
            'propriete': propriete,
            'loyer_total': loyer_total,
            'unites_locatives': unites_locatives
        })
    
    # Générer le récapitulatif KBIS
    html_recapitulatif = _generer_recapitulatif_kbis_html(
        recapitulatif, 
        totaux, 
        proprietes_avec_details
    )
    
    return HttpResponse(html_recapitulatif, content_type='text/html')


def _contrat_a_caution_avance_versee(contrat):
    """
    Vérifie si un contrat a reçu au moins un paiement de caution ou d'avance.
    
    RÈGLE MÉTIER :
    - Un locataire qui signe un contrat en mi-mois et verse sa caution/avance 
      ne doit PAS apparaître dans le récap de ce mois-là.
    - Mais une fois la caution/avance versée, il apparaît dans TOUS les récaps suivants,
      même s'il n'a pas encore payé le loyer du mois.
    
    OPTIMISATION:
    - Utilise les paiements préchargés si disponibles (via prefetch_related)
    - Sinon fait une requête DB classique
    
    Args:
        contrat: Le contrat à vérifier
    
    Returns:
        bool: True si le contrat a reçu au moins un paiement de caution ou avance validé
    """
    # OPTIMISATION: Vérifier si les paiements ont été préchargés
    if hasattr(contrat, 'paiements_caution_avance'):
        # Utiliser les paiements préchargés
        return len(contrat.paiements_caution_avance) > 0
    else:
        # Fallback: Faire une requête DB classique
        from paiements.models import Paiement
        return Paiement.objects.filter(
            contrat=contrat,
            type_paiement__in=['caution', 'avance'],
            statut='valide'
        ).exists()


def _generer_recapitulatif_kbis_html(recapitulatif, totaux, proprietes_avec_details):
    """Génère le HTML du récapitulatif KBIS A4 paysage."""
    
    # En-tête KBIS
    entete_kbis = """
    <div class="entete-principal">
        <div class="logo-section">
            <img src="/static/images/enteteEnImage.png" 
                 alt="KBIS IMMOBILIER" 
                 style="width: 100%; max-width: 100%; height: auto; display: block;">
        </div>
    </div>
    """
    
    # Pied de page dynamique
    try:
        from core.models import ConfigurationEntreprise
        config = ConfigurationEntreprise.get_configuration_active()
        
        pied_page = f"""
        <div class="pied-page" style="margin-top: 30px; padding: 20px; border-top: 2px solid #333; text-align: center; font-size: 12px; color: #666;">
            <div style="margin-bottom: 10px;">
                <strong>{config.nom_entreprise}</strong><br>
                {config.adresse}<br>
                Tél: {config.telephone} | Email: {config.email}
            </div>
            <div style="font-style: italic;">
                Document généré le {recapitulatif.date_creation.strftime('%d/%m/%Y à %H:%M')}
            </div>
        </div>
        """
    except:
        pied_page = f"""
        <div class="pied-page" style="margin-top: 30px; padding: 20px; border-top: 2px solid #333; text-align: center; font-size: 12px; color: #666;">
            <div style="font-style: italic;">
                Document généré le {recapitulatif.date_creation.strftime('%d/%m/%Y à %H:%M')}
            </div>
        </div>
        """
    
    # Contenu principal
    contenu = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Récapitulatif Mensuel - {recapitulatif.bailleur.get_nom_complet()}</title>
        <style>
            @page {{
                size: A4 landscape;
                margin: 1cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
                margin: 0;
                padding: 0;
            }}
            .entete-principal {{
                margin-bottom: 20px;
            }}
            .titre-principal {{
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
                color: #333;
            }}
            .info-bailleur {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .tableau-proprietes {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .tableau-proprietes th,
            .tableau-proprietes td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .tableau-proprietes th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            .tableau-proprietes .propriete-principale {{
                background-color: #e3f2fd;
                font-weight: bold;
            }}
            .tableau-proprietes .unite-locative {{
                background-color: #f5f5f5;
                padding-left: 20px;
            }}
            .totaux {{
                background-color: #e8f5e8;
                font-weight: bold;
            }}
            .montant {{
                text-align: right;
            }}
        </style>
    </head>
    <body>
        {entete_kbis}
        
        <div class="titre-principal">
            RÉCAPITULATIF MENSUEL - {recapitulatif.mois_recap.strftime('%B %Y').upper()}
        </div>
        
        <div class="info-bailleur">
            <h3>Bailleur: {recapitulatif.bailleur.get_nom_complet()}</h3>
            <p><strong>Période:</strong> {recapitulatif.mois_recap.strftime('%B %Y')}</p>
            <p><strong>Date de génération:</strong> {recapitulatif.date_creation.strftime('%d/%m/%Y à %H:%M')}</p>
        </div>
        
    """
    
    # Ajouter les propriétés groupées
    for item in proprietes_avec_details:
        propriete = item['propriete']
        loyer_total = item['loyer_total']
        unites_locatives = item['unites_locatives']
        
        # FILTRE : Vérifier si la propriété a au moins un locataire avec paiement complet
        # Avant d'afficher l'en-tête de la propriété, collecter les lignes de contrats valides
        lignes_contrats_html = []
        loyer_propriete_cumul = 0  # Loyer cumulé des contrats valides seulement
        
        # Ajouter les unités locatives de cette propriété
        if unites_locatives.exists():
            for unite in unites_locatives:
                contrats_actifs = unite.contrats_actifs
                if contrats_actifs.exists():
                    for contrat in contrats_actifs:
                        # FILTRE : N'afficher que les locataires ayant versé leur caution/avance initiale
                        if not _contrat_a_caution_avance_versee(contrat):
                            continue  # Sauter ce contrat si caution/avance non versée
                        
                        loyer_unite = contrat.loyer_mensuel or 0
                        charges_unite = contrat.charges_mensuelles or 0
                        total_unite = loyer_unite + charges_unite
                        locataire_nom = f"{contrat.locataire.nom} {contrat.locataire.prenom}" if contrat.locataire else "N/A"
                        
                        # Ajouter à la liste des lignes valides
                        lignes_contrats_html.append(f"""
                        <tr>
                            <td><strong>{unite.numero_unite}</strong> - {unite.nom}</td>
                            <td>{unite.type_unite}</td>
                            <td>Étage: {unite.etage} | {unite.surface}m²</td>
                            <td>{locataire_nom}</td>
                            <td class="montant">{loyer_unite:,.0f} F CFA</td>
                            <td class="montant">{charges_unite:,.0f} F CFA</td>
                            <td class="montant"><strong>{total_unite:,.0f} F CFA</strong></td>
                        </tr>
                        """)
                        loyer_propriete_cumul += loyer_unite
        else:
            # Propriété sans unités locatives (contrat direct sur la propriété)
            contrats_propriete = propriete.contrats.filter(est_actif=True, est_resilie=False)
            if contrats_propriete.exists():
                for contrat in contrats_propriete:
                    # FILTRE : N'afficher que les locataires ayant versé leur caution/avance initiale
                    if not _contrat_a_caution_avance_versee(contrat):
                        continue  # Sauter ce contrat si caution/avance non versée
                    
                    loyer_prop = contrat.loyer_mensuel or 0
                    charges_prop = contrat.charges_mensuelles or 0
                    total_prop = loyer_prop + charges_prop
                    locataire_nom = f"{contrat.locataire.nom} {contrat.locataire.prenom}" if contrat.locataire else "N/A"
                    
                    # Ajouter à la liste des lignes valides
                    lignes_contrats_html.append(f"""
                    <tr>
                        <td colspan="3"><strong>Propriété complète</strong></td>
                        <td>{locataire_nom}</td>
                        <td class="montant">{loyer_prop:,.0f} F CFA</td>
                        <td class="montant">{charges_prop:,.0f} F CFA</td>
                        <td class="montant"><strong>{total_prop:,.0f} F CFA</strong></td>
                    </tr>
                    """)
                    loyer_propriete_cumul += loyer_prop
        
        # N'afficher la propriété QUE si elle a au moins un contrat valide
        if len(lignes_contrats_html) > 0:
            # En-tête de la propriété
            contenu += f"""
        <div class="groupe-propriete" style="margin-bottom: 30px; page-break-inside: avoid;">
            <div class="entete-propriete" style="background-color: #2c3e50; color: white; padding: 15px; border-radius: 5px 5px 0 0; margin-top: 20px;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">{propriete.titre}</h3>
                <div style="font-size: 13px;">
                    <strong>Type:</strong> {propriete.type_bien.nom if propriete.type_bien else 'N/A'} | 
                    <strong>Adresse:</strong> {propriete.adresse} | 
                    <strong>Quartier:</strong> {propriete.quartier if hasattr(propriete, 'quartier') and propriete.quartier else propriete.ville or 'N/A'} |
                    <strong>Loyer Total:</strong> {loyer_propriete_cumul:,.0f} F CFA
                </div>
            </div>
            
            <table class="tableau-proprietes" style="margin-top: 0;">
                <thead>
                    <tr>
                        <th>Unité Locative</th>
                        <th>Type</th>
                        <th>Détails</th>
                        <th>Locataire</th>
                        <th>Loyer</th>
                        <th>Charges</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            # Ajouter toutes les lignes collectées
            for ligne_html in lignes_contrats_html:
                contenu += ligne_html
            
            # Sous-total pour la propriété
            contenu += f"""
                    <tr class="totaux" style="background-color: #e8f5e8;">
                        <td colspan="4" style="text-align: right;"><strong>SOUS-TOTAL PROPRIÉTÉ</strong></td>
                        <td class="montant"><strong>{loyer_propriete_cumul:,.0f} F CFA</strong></td>
                        <td class="montant"><strong>0 F CFA</strong></td>
                        <td class="montant"><strong>{loyer_propriete_cumul:,.0f} F CFA</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
    
    # Ajouter le tableau des totaux généraux
    contenu += f"""
        <div class="totaux-generaux" style="margin-top: 30px; padding: 20px; background-color: #e8f5e8; border-radius: 5px; border: 2px solid #27ae60;">
            <h3 style="margin: 0 0 15px 0; color: #27ae60; text-align: center;">TOTAUX GÉNÉRAUX</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #27ae60;"><strong>Total Loyers Bruts:</strong></td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #27ae60;"><strong>{totaux['total_loyers_bruts']:,.0f} F CFA</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #27ae60;"><strong>Total Charges Déductibles:</strong></td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #27ae60;"><strong>{totaux['total_charges_deductibles']:,.0f} F CFA</strong></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #27ae60;"><strong>Total Charges Bailleur:</strong></td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #27ae60;"><strong>{totaux['total_charges_bailleur']:,.0f} F CFA</strong></td>
                </tr>
                <tr style="background-color: #d4edda;">
                    <td style="padding: 15px; font-size: 16px;"><strong>NET À PAYER AU BAILLEUR:</strong></td>
                    <td style="padding: 15px; text-align: right; font-size: 16px;"><strong>{totaux['total_net_a_payer']:,.0f} F CFA</strong></td>
                </tr>
            </table>
        </div>
        
        <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
            <h4>Résumé du Récapitulatif</h4>
            <p><strong>Nombre de propriétés:</strong> {totaux['nombre_proprietes']}</p>
            <p><strong>Nombre de contrats actifs:</strong> {totaux['nombre_contrats_actifs']}</p>
            <p><strong>Nombre de paiements reçus:</strong> {totaux['nombre_paiements_recus']}</p>
        </div>
        
        {pied_page}
    </body>
    </html>
    """
    
    return contenu


@login_required
def valider_recapitulatif(request, recapitulatif_id):
    """Valider un récapitulatif mensuel."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    if not recapitulatif.peut_etre_valide():
        return JsonResponse({
            'success': False,
            'message': 'Ce récapitulatif ne peut pas être validé'
        })
    
    try:
        recapitulatif.valider(request.user)
        
        # Log de l'action
        logger.info(
            f"Récapitulatif {recapitulatif.pk} validé par {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Récapitulatif validé avec succès',
            'nouveau_statut': recapitulatif.get_statut_display(),
            'date_validation': recapitulatif.date_validation.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation du récapitulatif {recapitulatif.pk}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        })


@login_required
def envoyer_recapitulatif(request, recapitulatif_id):
    """Envoyer un récapitulatif mensuel au bailleur."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    if not recapitulatif.peut_etre_envoye():
        return JsonResponse({
            'success': False,
            'message': 'Ce récapitulatif ne peut pas être envoyé'
        })
    
    try:
        recapitulatif.envoyer_au_bailleur()
        
        # Log de l'action
        logger.info(
            f"Récapitulatif {recapitulatif.pk} envoyé par {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Récapitulatif marqué comme envoyé',
            'nouveau_statut': recapitulatif.get_statut_display(),
            'date_envoi': recapitulatif.date_envoi.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du récapitulatif {recapitulatif.pk}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de l\'envoi: {str(e)}'
        })


@login_required
def marquer_paye_recapitulatif(request, recapitulatif_id):
    """Marquer un récapitulatif mensuel comme payé."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    if not recapitulatif.peut_etre_paye():
        return JsonResponse({
            'success': False,
            'message': 'Ce récapitulatif ne peut pas être marqué comme payé'
        })
    
    try:
        recapitulatif.marquer_comme_paye()
        
        # Log de l'action
        logger.info(
            f"Récapitulatif {recapitulatif.pk} marqué comme payé par {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Récapitulatif marqué comme payé',
            'nouveau_statut': recapitulatif.get_statut_display(),
            'date_paiement': recapitulatif.date_paiement.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du marquage payé du récapitulatif {recapitulatif.pk}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du marquage: {str(e)}'
        })


@login_required
def telecharger_pdf_recapitulatif(request, recapitulatif_id):
    """Télécharger le PDF du récapitulatif mensuel."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    # Vérifier que le bailleur existe
    if not recapitulatif.bailleur:
        messages.error(request, 'Ce récapitulatif n\'a pas de bailleur associé. Impossible de générer le PDF.')
        return redirect('paiements:detail_recapitulatif', recapitulatif_id=recapitulatif_id)
    
    try:
        # Générer le PDF
        pdf_content = recapitulatif.generer_pdf_recapitulatif(user=request.user)
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{recapitulatif.get_nom_fichier_pdf()}"'
        
        # Log de l'action
        logger.info(
            f"PDF du récapitulatif {recapitulatif.pk} téléchargé par {request.user.username}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF du récapitulatif {recapitulatif.pk}: {e}")
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('paiements:detail_recapitulatif', recapitulatif.pk)


@login_required
def apercu_recapitulatif(request, recapitulatif_id):
    """Aperçu HTML du récapitulatif mensuel."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    try:
        recapitulatif = RecapMensuel.objects.select_related('bailleur').get(pk=recapitulatif_id)
        
        # Forcer le recalcul des totaux pour s'assurer qu'ils sont à jour et dynamiques
        # Rafraîchir l'objet depuis la base de données pour éviter les problèmes de cache
        recapitulatif.refresh_from_db()
        
        # Calculer les totaux (cette méthode sauvegarde aussi les valeurs)
        totaux = recapitulatif.calculer_totaux_bailleur()
        
        # Vérifier que les totaux sont valides
        if not totaux:
            totaux = {
                'total_loyers_bruts': Decimal('0'),
                'total_charges_deductibles': Decimal('0'),
                'total_charges_bailleur': Decimal('0'),
                'total_net_a_payer': Decimal('0'),
                'commission_agence': Decimal('0'),
                'montant_reellement_paye': Decimal('0'),
                'nombre_proprietes': 0,
                'nombre_contrats_actifs': 0,
                'nombre_paiements_recus': 0,
                'nombre_bailleurs': 1 if recapitulatif.bailleur else 0,
            }
        # S'assurer que commission_agence et montant_reellement_paye sont présents
        # Utiliser getattr pour éviter les erreurs si les migrations ne sont pas encore appliquées
        if 'commission_agence' not in totaux:
            totaux['commission_agence'] = getattr(recapitulatif, 'commission_agence', None) or Decimal('0')
        if 'montant_reellement_paye' not in totaux:
            totaux['montant_reellement_paye'] = getattr(recapitulatif, 'montant_reellement_paye', None) or Decimal('0')
        
        context = {
            'recapitulatif': recapitulatif,
            'totaux': totaux,
            'date_generation': timezone.now(),
            'apercu': True
        }
        
        return render(request, 'paiements/recapitulatifs/apercu_recapitulatif.html', context)
        
    except RecapMensuel.DoesNotExist:
        messages.error(request, f"Récapitulatif avec l'ID {recapitulatif_id} introuvable.")
        return redirect('paiements:liste_recaps_mensuels')
    except Exception as e:
        messages.error(request, f"Erreur lors de l'affichage du récapitulatif: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels')


@login_required
def statistiques_recapitulatifs(request):
    """Statistiques des récapitulatifs mensuels."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Statistiques par mois
    stats_mensuelles = RecapMensuel.objects.values('mois_recap').annotate(
        nombre=Count('id')
    ).order_by('-mois_recap')[:12]
    
    # Calculer les totaux pour chaque mois
    for stat in stats_mensuelles:
        mois = stat['mois_recap']
        recapitulatifs_mois = RecapMensuel.objects.filter(mois_recap=mois)
        
        from decimal import Decimal
        total_loyers = Decimal('0')
        total_charges = Decimal('0')
        total_net = Decimal('0')
        
        for recap in recapitulatifs_mois:
            totaux = recap.calculer_totaux_globaux()
            total_loyers += totaux['total_loyers_bruts']
            total_charges += totaux['total_charges_deductibles']
            total_net += totaux['total_net_a_payer']
        
        stat['total_loyers'] = total_loyers
        stat['total_charges'] = total_charges
        stat['total_net'] = total_net
    
    # Statistiques par statut
    stats_statut = RecapMensuel.objects.values('statut').annotate(
        nombre=Count('id')
    ).order_by('statut')
    
    # Statistiques par type - removed as RecapMensuel model doesn't have type_recapitulatif field
    stats_type = []
    
    context = {
        'page_title': 'Statistiques des Récapitulatifs',
        'page_icon': 'graph-up',
        'stats_mensuelles': stats_mensuelles,
        'stats_statut': stats_statut,
        'stats_type': stats_type
    }
    
    return render(request, 'paiements/recapitulatifs/statistiques_recapitulatifs.html', context)


@login_required
def creer_recapitulatif_test(request):
    """Créer un récapitulatif de test pour résoudre le problème 404."""
    
    # Vérification des permissions
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    try:
        from datetime import date
        
        # Vérifier s'il y a des bailleurs
        if not Bailleur.objects.exists():
            messages.error(request, "Aucun bailleur trouvé. Veuillez d'abord créer des bailleurs.")
            return redirect('paiements:liste_recaps_mensuels')
        
        # Prendre le premier bailleur disponible
        bailleur = Bailleur.objects.first()
        
        # Créer un récapitulatif de test
        recapitulatif = RecapMensuel.objects.create(
            bailleur=bailleur,
            mois_recap=date.today().replace(day=1),
            statut='brouillon',
            cree_par=request.user,
            garanties_suffisantes=True
        )
        
        messages.success(request, f"Récapitulatif de test créé avec l'ID {recapitulatif.id}")
        return redirect('paiements:apercu_recapitulatif', recapitulatif.id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création du récapitulatif de test: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels')


@login_required
def generer_recapitulatif_automatique(request):
    """Générer automatiquement le récapitulatif du mois en cours."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    try:
        # Récupérer le bailleur depuis les paramètres POST
        from proprietes.models import Bailleur
        bailleur_id = request.POST.get('bailleur_id')
        
        if not bailleur_id:
            return JsonResponse({
                'success': False,
                'message': 'Un bailleur est requis pour créer un récapitulatif'
            })
        
        try:
            bailleur = Bailleur.objects.get(id=bailleur_id, is_deleted=False)
        except Bailleur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Bailleur introuvable'
            })
        
        # Vérifier s'il existe déjà un récapitulatif pour ce mois et ce bailleur
        mois_actuel = timezone.now().replace(day=1)
        
        if RecapMensuel.objects.filter(
            bailleur=bailleur,
            mois_recap=mois_actuel,
            is_deleted=False
        ).exists():
            return JsonResponse({
                'success': False,
                'message': f'Un récapitulatif mensuel existe déjà pour {bailleur.get_nom_complet()} - {mois_actuel.strftime("%B %Y")}'
            })
        
        # Créer le récapitulatif automatiquement avec le bailleur
        recapitulatif = RecapMensuel.objects.create(
            bailleur=bailleur,
            mois_recap=mois_actuel,
            cree_par=request.user,
            garanties_suffisantes=True
        )
        
        # Log de l'action
        logger.info(
            f"Récapitulatif automatique {recapitulatif.pk} créé par {request.user.username} "
            f"pour {mois_actuel.strftime('%B %Y')}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Récapitulatif automatique créé pour {mois_actuel.strftime("%B %Y")}',
            'recapitulatif_id': recapitulatif.pk,
            'redirect_url': reverse('paiements:detail_recapitulatif', args=[recapitulatif.pk])
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération automatique du récapitulatif: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la génération: {str(e)}'
        })


def _generer_pdf_recap_locataires_batch(bailleur, mois_recap, locataires_batch, page_num, total_pages, entete_base64, entete_mime="jpeg"):
    """
    Génère un PDF via WeasyPrint (supporte rowspan/CSS complexe, bien plus léger que xhtml2pdf).
    """
    import datetime
    from django.template.loader import render_to_string
    from .services_recap_paiement import MOIS_FRANCAIS

    LOCATAIRES_PAR_PAGE = 8
    mois_display = f"{MOIS_FRANCAIS.get(mois_recap.month, '')} {mois_recap.year}" if hasattr(mois_recap, 'month') else str(mois_recap)
    recap_data = {
        'bailleur_nom': bailleur.get_nom_complet() if hasattr(bailleur, 'get_nom_complet') else str(bailleur),
        'bailleur_telephone': getattr(bailleur, 'telephone', None) or 'Non renseigné',
        'bailleur_email': getattr(bailleur, 'email', None) or 'Non renseigné',
        'bailleur_adresse': getattr(bailleur, 'adresse', None) or 'Non renseignée',
        'mois_recap': mois_recap,
        'mois_display': mois_display,
        'locataires': locataires_batch,
        'total_locataires': len(locataires_batch),
        'total_reglees': sum(1 for l in locataires_batch if l.get('statut_global') == 'regle'),
        'total_en_retard': sum(1 for l in locataires_batch if l.get('statut_global') == 'en_retard'),
        'limit_truncated': False,
        'page_num': page_num,
        'total_pages': total_pages,
        'page_offset': (page_num - 1) * LOCATAIRES_PAR_PAGE,
    }
    date_generation = datetime.datetime.now()
    html_content = render_to_string(
        'paiements/recapitulatifs/recap_locataires_paysage.html',
        {'recap': recap_data, 'date_generation': date_generation, 'entete_base64': entete_base64, 'entete_mime': entete_mime}
    )
    # WeasyPrint sur Linux/Render (gère rowspan/CSS, très léger en mémoire).
    # Sur Windows dev, les libs GTK sont absentes → fallback xhtml2pdf.
    import sys
    _use_weasyprint = sys.platform != 'win32'
    if _use_weasyprint:
        try:
            from weasyprint import HTML
            return HTML(string=html_content, base_url=None).write_pdf()
        except Exception:
            _use_weasyprint = False

    # Fallback xhtml2pdf (dev Windows ou si WeasyPrint échoue)
    from io import BytesIO
    from xhtml2pdf import pisa
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html_content, dest=pdf_buffer, encoding='UTF-8', link_callback=None)
    return pdf_buffer.getvalue()


@login_required
def generer_recap_paiement_mensuel(request, bailleur_id):
    """
    Génère un récapitulatif PDF des locataires. Pagination: si >15 locataires,
    génère plusieurs PDFs dans un ZIP pour éviter OOM sur Render.
    """
    import datetime
    import zipfile
    from dateutil.relativedelta import relativedelta
    from io import BytesIO
    from core.utils import check_group_permissions_with_fallback
    
    LOCATAIRES_PAR_PAGE = 8  # Limite mémoire Render 512MB (1 worker)
    
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 
        'view'
    )
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # Récupérer le mois depuis les paramètres GET (par défaut mois courant)
    # Le mois courant reflète l'état réel : on part du dernier mois réglé en base
    # pour chaque locataire, jusqu'à aujourd'hui.
    mois_str = request.GET.get('mois')
    if mois_str:
        try:
            mois_recap = datetime.datetime.strptime(mois_str, '%Y-%m').date().replace(day=1)
        except ValueError:
            mois_recap = datetime.date.today().replace(day=1)
    else:
        # Par défaut, mois courant (situation réelle à la date d'aujourd'hui)
        mois_recap = datetime.date.today().replace(day=1)

    try:
        # Préparer les données du récapitulatif par locataire
        recap_data = ServiceRecapPaiementMensuel.preparer_donnees_recap_locataires(
            bailleur, mois_recap
        )
        
        # Forcer les données à être des listes Python standard pour éviter les erreurs NotImplementedType
        if not isinstance(recap_data, dict):
            logger.error(f"recap_data n'est pas un dictionnaire: {type(recap_data)}")
            raise ValueError("Les données du récapitulatif sont invalides")
        
        if 'locataires' in recap_data:
            recap_data['locataires'] = _force_list_safe(recap_data['locataires'])
            # Pour chaque locataire, forcer les contrats à être une liste
            for locataire_data in recap_data['locataires']:
                if not isinstance(locataire_data, dict):
                    logger.warning(f"locataire_data n'est pas un dictionnaire: {type(locataire_data)}")
                    continue
                if 'contrats' in locataire_data:
                    locataire_data['contrats'] = _force_list_safe(locataire_data['contrats'])
                else:
                    locataire_data['contrats'] = []
        else:
            recap_data['locataires'] = []
        
        # S'assurer que tous les champs nécessaires existent
        if 'total_locataires' not in recap_data:
            recap_data['total_locataires'] = 0
        if 'total_reglees' not in recap_data:
            recap_data['total_reglees'] = 0
        if 'total_en_retard' not in recap_data:
            recap_data['total_en_retard'] = 0
        
        # Générer le HTML du récapitulatif avec date correcte
        date_generation = datetime.datetime.now()
        
        # S'assurer que recap_data['locataires'] est une liste itérable
        # et que chaque élément a une liste de contrats
        locataires_list = []
        try:
            locataires_raw = recap_data.get('locataires', [])
            # Forcer en liste si ce n'est pas déjà une liste
            if not isinstance(locataires_raw, list):
                locataires_raw = _force_list_safe(locataires_raw)
            
            for locataire_data in locataires_raw:
                if not isinstance(locataire_data, dict):
                    logger.warning(f"locataire_data n'est pas un dict: {type(locataire_data)}")
                    continue
                
                # S'assurer que 'contrats' est une liste
                contrats_list = []
                contrats_raw = locataire_data.get('contrats', [])
                if not isinstance(contrats_raw, list):
                    contrats_raw = _force_list_safe(contrats_raw)
                
                for contrat_data in contrats_raw:
                    if isinstance(contrat_data, dict):
                        contrats_list.append(contrat_data)
                
                locataire_data['contrats'] = contrats_list
                locataires_list.append(locataire_data)
            
            recap_data['locataires'] = locataires_list
            recap_data['limit_truncated'] = False
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des locataires: {e}", exc_info=True)
            recap_data['locataires'] = []
            recap_data['limit_truncated'] = False
        
        # Charger l'image en Base64 — convertie en JPEG RGB (pas d'alpha) pour éviter OOM
        # xhtml2pdf/PIL plantent sur canal alpha (RGBA PNG) avec peu de RAM (Render free tier)
        import os
        import base64
        from io import BytesIO
        from django.conf import settings
        entete_base64 = ""
        entete_mime = "jpeg"
        image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'enteteEnImage.png')
        if os.path.exists(image_path):
            try:
                from PIL import Image
                img = Image.open(image_path)
                # Réduire la taille : 800px max de large
                max_w = 800
                if img.width > max_w:
                    ratio = max_w / img.width
                    img = img.resize((max_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
                # Convertir en RGB (supprime canal alpha qui cause le crash PIL/xhtml2pdf)
                if img.mode in ('RGBA', 'LA', 'P', 'PA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                buf = BytesIO()
                img.save(buf, format='JPEG', quality=70, optimize=True)
                entete_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                entete_mime = "jpeg"
                buf.close()
                del img
            except Exception as e:
                logger.warning(f"Image en-tête ignorée (erreur PIL): {e}")
                entete_base64 = ""
        
        # Pagination: générer un PDF par lot de 15 locataires
        locataires_list = recap_data['locataires']
        total_loc = len(locataires_list)
        total_pages = (total_loc + LOCATAIRES_PAR_PAGE - 1) // LOCATAIRES_PAR_PAGE if total_loc > 0 else 1
        
        pdfs_generes = []
        base_filename = f"recap_paiement_{bailleur.get_nom_complet().replace(' ', '_')}_{mois_recap.strftime('%Y_%m')}"
        
        for page in range(total_pages):
            debut = page * LOCATAIRES_PAR_PAGE
            fin = min(debut + LOCATAIRES_PAR_PAGE, total_loc)
            batch = locataires_list[debut:fin]
            try:
                pdf_content = _generer_pdf_recap_locataires_batch(
                    bailleur, mois_recap, batch, page + 1, total_pages, entete_base64, entete_mime
                )
                pdfs_generes.append((f"{base_filename}_page{page + 1}.pdf", pdf_content))
            except Exception as pdf_err:
                logger.error(f"Erreur PDF page {page + 1}: {pdf_err}", exc_info=True)
                messages.error(request, f"Erreur lors de la génération du PDF (page {page + 1}): {str(pdf_err)}")
                return redirect('paiements:dashboard')
            import gc
            gc.collect()
        
        # Fusionner tous les PDFs en un seul fichier (fin du ZIP multi-pages)
        if total_pages == 1:
            pdf_final = pdfs_generes[0][1]
        else:
            from pypdf import PdfWriter, PdfReader
            writer = PdfWriter()
            for _, contenu in pdfs_generes:
                reader = PdfReader(BytesIO(contenu))
                for page in reader.pages:
                    writer.add_page(page)
            merged_buf = BytesIO()
            writer.write(merged_buf)
            pdf_final = merged_buf.getvalue()

        response = HttpResponse(pdf_final, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{base_filename}.pdf"'
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du récapitulatif de paiement: {str(e)}", exc_info=True)
        messages.error(request, f"Erreur lors de la génération: {str(e)}")
        return redirect('paiements:dashboard')


@login_required
def generer_pdf_recap_paiement_mensuel_paysage(request, bailleur_id):
    """
    Génère un récapitulatif PDF A4 paysage de l'état de paiement mensuel pour un bailleur.
    Utilise les données réelles du récapitulatif avec le même format et style que le récap détaillé.
    """
    import datetime
    from dateutil.relativedelta import relativedelta
    from django.template.loader import render_to_string
    from io import BytesIO
    from xhtml2pdf import pisa
    from core.utils import check_group_permissions_with_fallback
    
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 
        'view'
    )
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # Récupérer le mois depuis les paramètres GET (par défaut mois courant)
    # Le mois courant reflète l'état réel : on part du dernier mois réglé en base
    # pour chaque locataire, jusqu'à aujourd'hui.
    mois_str = request.GET.get('mois')
    if mois_str:
        try:
            mois_recap = datetime.datetime.strptime(mois_str, '%Y-%m').date().replace(day=1)
        except ValueError:
            mois_recap = datetime.date.today().replace(day=1)
    else:
        # Par défaut, mois courant (situation réelle à la date d'aujourd'hui)
        mois_recap = datetime.date.today().replace(day=1)

    try:
        # Préparer les données du récapitulatif avec les données réelles
        recap_data = ServiceRecapPaiementMensuel.preparer_donnees_recap_paiement(
            bailleur, mois_recap
        )
        
        # Générer le HTML du récapitulatif avec date correcte
        date_generation = datetime.datetime.now()
        
        # Récupérer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        entreprise_config = ConfigurationEntreprise.get_configuration_active()
        
        html_content = render_to_string(
            'paiements/recapitulatifs/recap_paiement_mensuel_paysage.html',
            {
                'recap': recap_data,
                'date_generation': date_generation,
                'entreprise_config': entreprise_config,
            }
        )
        
        # Générer le PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_buffer,
            encoding='UTF-8'
        )
        
        if pisa_status.err:
            logger.error(f"Erreur lors de la génération PDF paysage: {pisa_status.err}")
            messages.error(request, f"Erreur lors de la génération du PDF: {pisa_status.err}")
            return redirect('paiements:dashboard')
        
        # Préparer la réponse
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = (
            f"etat_paiements_mensuels_{bailleur.get_nom_complet().replace(' ', '_')}_"
            f"{mois_recap.strftime('%Y_%m')}.pdf"
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF du récapitulatif pour le bailleur {bailleur_id}: {e}", exc_info=True)
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('paiements:dashboard')


@login_required
def generer_pdf_recap_locataires_paysage(request, bailleur_id):
    """
    Alias: même logique que generer_recap_paiement_mensuel (pagination par 15 locataires).
    """
    return generer_recap_paiement_mensuel(request, bailleur_id)


