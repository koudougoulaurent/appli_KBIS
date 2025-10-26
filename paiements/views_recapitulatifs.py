#!/usr/bin/env python3
"""
Vues pour la gestion des récapitulatifs mensuels
================================================

Ce module gère la création, validation et envoi des récapitulatifs mensuels
qui résument toutes les opérations financières pour chaque bailleur.
"""

import logging
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
from proprietes.models import Bailleur

logger = logging.getLogger(__name__)


@login_required
def liste_recapitulatifs(request):
    """Liste de tous les récapitulatifs mensuels."""
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Filtres
    mois = request.GET.get('mois')
    statut = request.GET.get('statut')
    type_recap = request.GET.get('type')
    
    recapitulatifs = RecapMensuel.objects.all()
    
    # Appliquer les filtres
    if mois:
        recapitulatifs = recapitulatifs.filter(mois_recap__icontains=mois)
    if statut:
        recapitulatifs = recapitulatifs.filter(statut=statut)
    # Note: type_recap filter removed as RecapMensuel model doesn't have type_recapitulatif field
    
    # Pagination
    paginator = Paginator(recapitulatifs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': recapitulatifs.count(),
        'en_preparation': recapitulatifs.filter(statut='en_preparation').count(),
        'valides': recapitulatifs.filter(statut='valide').count(),
        'envoyes': recapitulatifs.filter(statut='envoye').count(),
        'payes': recapitulatifs.filter(statut='paye').count(),
    }
    
    context = {
        'page_title': 'Récapitulatifs Mensuels',
        'page_icon': 'file-earmark-text',
        'page_obj': page_obj,
        'stats': stats,
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
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    # Calculer les totaux (version simplifiée)
    totaux = {
        'total_loyers_bruts': recapitulatif.total_loyers_bruts,
        'total_charges_deductibles': recapitulatif.total_charges_deductibles,
        'total_charges_bailleur': recapitulatif.total_charges_bailleur,
        'total_net_a_payer': recapitulatif.total_net_a_payer,
        'nombre_proprietes': recapitulatif.nombre_proprietes,
        'nombre_contrats_actifs': recapitulatif.nombre_contrats_actifs,
        'nombre_paiements_recus': recapitulatif.nombre_paiements_recus,
    }
    
    context = {
        'page_title': f'Récapitulatif - {recapitulatif.mois_recap.strftime("%B %Y")}',
        'page_icon': 'file-earmark-text',
        'recapitulatif': recapitulatif,
        'totaux': totaux
    }
    
    return render(request, 'paiements/recapitulatifs/detail_recapitulatif.html', context)


@login_required
def generer_recapitulatif_kbis(request, recapitulatif_id):
    """Génère un récapitulatif A4 paysage avec en-tête KBIS et pied de page dynamique."""
    
    # Vérification des permissions
    from core.utils import check_group_permissions_with_fallback
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    recapitulatif = get_object_or_404(RecapMensuel, pk=recapitulatif_id)
    
    # Calculer les totaux
    totaux = recapitulatif.calculer_totaux_bailleur()
    
    # Récupérer les propriétés du bailleur avec leurs unités locatives
    proprietes = recapitulatif.bailleur.proprietes.filter(
        is_deleted=False
    ).select_related('type_bien').prefetch_related(
        'unites_locatives__contrats__locataire'
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
        
        <table class="tableau-proprietes">
            <thead>
                <tr>
                    <th>Propriété</th>
                    <th>Type</th>
                    <th>Adresse</th>
                    <th>Loyer Brut</th>
                    <th>Charges Déductibles</th>
                    <th>Charges Bailleur</th>
                    <th>Net à Payer</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Ajouter les propriétés
    for item in proprietes_avec_details:
        propriete = item['propriete']
        loyer_total = item['loyer_total']
        unites_locatives = item['unites_locatives']
        
        # Ligne principale de la propriété
        contenu += f"""
                <tr class="propriete-principale">
                    <td><strong>{propriete.titre}</strong></td>
                    <td>{propriete.type_bien.nom if propriete.type_bien else 'N/A'}</td>
                    <td>{propriete.adresse}</td>
                    <td class="montant">{loyer_total:,.0f} F CFA</td>
                    <td class="montant">0 F CFA</td>
                    <td class="montant">0 F CFA</td>
                    <td class="montant">{loyer_total:,.0f} F CFA</td>
                </tr>
        """
        
        # Ajouter les unités locatives si elles existent
        for unite in unites_locatives:
            contrats_actifs = unite.contrats_actifs
            if contrats_actifs.exists():
                for contrat in contrats_actifs:
                    loyer_unite = contrat.loyer_mensuel or 0
                    charges_unite = contrat.charges_mensuelles or 0
                    total_unite = loyer_unite + charges_unite
                    
                    contenu += f"""
                    <tr class="unite-locative">
                        <td>└─ {unite.numero_unite} - {unite.nom}</td>
                        <td>{unite.type_unite}</td>
                        <td>{unite.etage} - {unite.surface}m²</td>
                        <td class="montant">{loyer_unite:,.0f} F CFA</td>
                        <td class="montant">{charges_unite:,.0f} F CFA</td>
                        <td class="montant">0 F CFA</td>
                        <td class="montant">{total_unite:,.0f} F CFA</td>
                    </tr>
                    """
            else:
                loyer_unite = unite.loyer_mensuel or 0
                charges_unite = unite.charges_mensuelles or 0
                total_unite = loyer_unite + charges_unite
                
                contenu += f"""
                <tr class="unite-locative">
                    <td>└─ {unite.numero_unite} - {unite.nom}</td>
                    <td>{unite.type_unite}</td>
                    <td>{unite.etage} - {unite.surface}m²</td>
                    <td class="montant">{loyer_unite:,.0f} F CFA</td>
                    <td class="montant">{charges_unite:,.0f} F CFA</td>
                    <td class="montant">0 F CFA</td>
                    <td class="montant">{total_unite:,.0f} F CFA</td>
                </tr>
                """
    
    # Ajouter les totaux
    contenu += f"""
                <tr class="totaux">
                    <td colspan="3"><strong>TOTAL GÉNÉRAL</strong></td>
                    <td class="montant"><strong>{totaux['total_loyers_bruts']:,.0f} F CFA</strong></td>
                    <td class="montant"><strong>{totaux['total_charges_deductibles']:,.0f} F CFA</strong></td>
                    <td class="montant"><strong>{totaux['total_charges_bailleur']:,.0f} F CFA</strong></td>
                    <td class="montant"><strong>{totaux['total_net_a_payer']:,.0f} F CFA</strong></td>
                </tr>
            </tbody>
        </table>
        
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
        recapitulatif = RecapMensuel.objects.get(pk=recapitulatif_id)
        totaux = recapitulatif.calculer_totaux_bailleur()
        
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
        # Vérifier s'il existe déjà un récapitulatif pour ce mois
        mois_actuel = timezone.now().replace(day=1)
        
        if RecapMensuel.objects.filter(
            mois_recap=mois_actuel
        ).exists():
            return JsonResponse({
                'success': False,
                'message': f'Un récapitulatif mensuel existe déjà pour {mois_actuel.strftime("%B %Y")}'
            })
        
        # Créer le récapitulatif automatiquement
        recapitulatif = RecapMensuel.objects.create(
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
