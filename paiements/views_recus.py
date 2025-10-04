#!/usr/bin/env python
"""
Vues pour la gestion des reçus de récapitulatifs
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

# from .models import RecuRecapitulatif, RecapitulatifMensuelBailleur  # Modèles supprimés
from core.utils import check_group_permissions

logger = logging.getLogger(__name__)


@login_required
def liste_recus_recapitulatifs(request):
    """Liste des reçus de récapitulatifs."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Filtres
    statut_filter = request.GET.get('statut', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    # Requête de base
    recus = RecuRecapitulatif.objects.select_related(
        'recapitulatif__bailleur',
        'cree_par',
        'imprime_par'
    ).order_by('-date_creation')
    
    # Appliquer les filtres
    if statut_filter:
        recus = recus.filter(statut=statut_filter)
    
    if type_filter:
        recus = recus.filter(type_recu=type_filter)
    
    if search_query:
        recus = recus.filter(
            Q(numero_recu__icontains=search_query) |
            Q(recapitulatif__bailleur__nom__icontains=search_query) |
            Q(recapitulatif__bailleur__prenom__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(recus, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': RecuRecapitulatif.objects.count(),
        'imprimes': RecuRecapitulatif.objects.filter(imprime=True).count(),
        'envoyes': RecuRecapitulatif.objects.filter(envoye=True).count(),
        'valides': RecuRecapitulatif.objects.filter(statut='valide').count(),
    }
    
    context = {
        'page_title': 'Reçus de Récapitulatifs',
        'page_icon': 'receipt',
        'page_obj': page_obj,
        'stats': stats,
        'statut_filter': statut_filter,
        'type_filter': type_filter,
        'search_query': search_query,
        'statut_choices': RecuRecapitulatif._meta.get_field('statut').choices,
        'type_choices': RecuRecapitulatif._meta.get_field('type_recu').choices,
    }
    
    return render(request, 'paiements/recus/liste_recus_recapitulatifs.html', context)


@login_required
def detail_recu_recapitulatif(request, pk):
    """Détail d'un reçu de récapitulatif."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    # Calculer les totaux du récapitulatif
    totaux = recu.recapitulatif.calculer_totaux_bailleur()
    
    context = {
        'page_title': f'Reçu {recu.numero_recu}',
        'page_icon': 'receipt',
        'recu': recu,
        'totaux': totaux,
    }
    
    return render(request, 'paiements/recus/detail_recu_recapitulatif.html', context)


@login_required
def creer_recu_recapitulatif(request, recapitulatif_id):
    """Créer un reçu pour un récapitulatif."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    # Vérifier si un reçu existe déjà
    if hasattr(recapitulatif, 'recu'):
        messages.info(request, f'Un reçu existe déjà pour ce récapitulatif: {recapitulatif.recu.numero_recu}')
        return redirect('paiements:detail_recu_recapitulatif', pk=recapitulatif.recu.pk)
    
    if request.method == 'POST':
        try:
            # Créer le reçu
            recu = RecuRecapitulatif.objects.create(
                recapitulatif=recapitulatif,
                type_recu=request.POST.get('type_recu', 'recapitulatif'),
                template_utilise=request.POST.get('template_utilise', 'professionnel'),
                format_impression=request.POST.get('format_impression', 'A4_paysage'),
                cree_par=request.user,
                notes=request.POST.get('notes', '')
            )
            
            # Générer le hash de sécurité
            recu.generer_hash_securite()
            
            messages.success(request, f'Reçu créé avec succès: {recu.numero_recu}')
            return redirect('paiements:detail_recu_recapitulatif', pk=recu.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du reçu: {str(e)}')
            logger.error(f"Erreur création reçu: {str(e)}")
    
    context = {
        'page_title': 'Créer un Reçu',
        'page_icon': 'plus-circle',
        'recapitulatif': recapitulatif,
        'type_choices': RecuRecapitulatif._meta.get_field('type_recu').choices,
        'template_choices': RecuRecapitulatif._meta.get_field('template_utilise').choices,
        'format_choices': RecuRecapitulatif._meta.get_field('format_impression').choices,
    }
    
    return render(request, 'paiements/recus/creer_recu_recapitulatif.html', context)


@login_required
def imprimer_recu_recapitulatif(request, pk):
    """Imprimer un reçu de récapitulatif en PDF."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    try:
        # Calculer les totaux
        totaux = recu.recapitulatif.calculer_totaux_bailleur()
        
        # Rendre le template HTML
        html_content = render_to_string(
            'paiements/recus/recu_recapitulatif_professionnel.html',
            {
                'recu': recu,
                'totaux': totaux,
                'date_generation': timezone.now(),
            }
        )
        
        # Créer la réponse PDF avec reportlab
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centré
        )
        story.append(Paragraph(f"Reçu de Récapitulatif - {recu.numero_recu}", title_style))
        story.append(Spacer(1, 12))
        
        # Informations du reçu
        info_data = [
            ['Numéro de reçu:', recu.numero_recu],
            ['Date:', recu.date_creation.strftime('%d/%m/%Y')],
            ['Montant:', f"{recu.montant:,.0f} FCFA"],
            ['Type:', recu.get_type_display()],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Construire le PDF
        doc.build(story)
        
        # Marquer comme imprimé
        recu.marquer_imprime(request.user)
        
        # Préparer la réponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        filename = f"recu_recapitulatif_{recu.numero_recu}_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        pdf_buffer.close()
        
        messages.success(request, f'Reçu imprimé avec succès: {recu.numero_recu}')
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'impression: {str(e)}')
        logger.error(f"Erreur impression reçu: {str(e)}")
        return redirect('paiements:detail_recu_recapitulatif', pk=pk)


@login_required
def imprimer_recu_recapitulatif_gestimmob(request, pk):
    """Imprimer un reçu de récapitulatif avec le template GESTIMMOB."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    try:
        # Calculer les totaux et détails
        totaux = recu.recapitulatif.calculer_totaux_bailleur()
        
        # Récupérer la configuration de l'entreprise depuis la base de données
        from core.models import ConfigurationEntreprise
        config_entreprise = ConfigurationEntreprise.get_configuration_active()
        
        # Créer un objet config compatible avec le template
        config = {
            'nom_entreprise': config_entreprise.nom_entreprise,
            'slogan': config_entreprise.slogan or 'Gestion Immobilière Professionnelle',
            'couleur_principale': config_entreprise.couleur_principale,
            'couleur_secondaire': config_entreprise.couleur_secondaire,
            'logo_url': config_entreprise.logo_url,
            'get_adresse_complete': config_entreprise.get_adresse_complete(),
            'telephone': config_entreprise.telephone,
            'email': config_entreprise.email,
            'site_web': config_entreprise.site_web,
            'get_informations_legales': config_entreprise.get_informations_legales(),
        }
        
        # Rendre le template HTML GESTIMMOB
        html_content = render_to_string(
            'paiements/recus/recu_recapitulatif_gestimmob.html',
            {
                'recu': recu,
                'totaux': totaux,
                'config': config,
                'date_generation': timezone.now(),
            }
        )
        
        # Créer la réponse PDF avec reportlab
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centré
        )
        story.append(Paragraph(f"Reçu de Récapitulatif - {recu.numero_recu}", title_style))
        story.append(Spacer(1, 12))
        
        # Informations du reçu
        info_data = [
            ['Numéro de reçu:', recu.numero_recu],
            ['Date:', recu.date_creation.strftime('%d/%m/%Y')],
            ['Montant:', f"{recu.montant:,.0f} FCFA"],
            ['Type:', recu.get_type_display()],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Construire le PDF
        doc.build(story)
        
        # Marquer comme imprimé
        recu.marquer_imprime(request.user)
        
        # Préparer la réponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        filename = f"recu_recapitulatif_gestimmob_{recu.numero_recu}_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        pdf_buffer.close()
        
        messages.success(request, f'Reçu GESTIMMOB imprimé avec succès: {recu.numero_recu}')
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'impression: {str(e)}')
        logger.error(f"Erreur impression reçu GESTIMMOB: {str(e)}")
        return redirect('paiements:detail_recu_recapitulatif', pk=pk)


@login_required
def apercu_recu_recapitulatif_gestimmob(request, pk):
    """Aperçu du reçu de récapitulatif avec le template GESTIMMOB."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    try:
        # Calculer les totaux et détails
        totaux = recu.recapitulatif.calculer_totaux_bailleur()
        
        # Récupérer la configuration de l'entreprise depuis la base de données
        from core.models import ConfigurationEntreprise
        config_entreprise = ConfigurationEntreprise.get_configuration_active()
        
        # Créer un objet config compatible avec le template
        config = {
            'nom_entreprise': config_entreprise.nom_entreprise,
            'slogan': config_entreprise.slogan or 'Gestion Immobilière Professionnelle',
            'couleur_principale': config_entreprise.couleur_principale,
            'couleur_secondaire': config_entreprise.couleur_secondaire,
            'logo_url': config_entreprise.logo_url,
            'get_adresse_complete': config_entreprise.get_adresse_complete(),
            'telephone': config_entreprise.telephone,
            'email': config_entreprise.email,
            'site_web': config_entreprise.site_web,
            'get_informations_legales': config_entreprise.get_informations_legales(),
        }
        
        context = {
            'page_title': f'Aperçu Reçu GESTIMMOB - {recu.numero_recu}',
            'page_icon': 'receipt',
            'recu': recu,
            'totaux': totaux,
            'config': config,
            'date_generation': timezone.now(),
        }
        
        return render(request, 'paiements/recus/apercu_recu_recapitulatif_gestimmob.html', context)
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'aperçu: {str(e)}')
        logger.error(f"Erreur aperçu reçu GESTIMMOB: {str(e)}")
        return redirect('paiements:detail_recu_recapitulatif', pk=pk)


@login_required
def creer_recu_gestimmob_recapitulatif(request, recapitulatif_id):
    """Créer un reçu GESTIMMOB pour un récapitulatif."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recapitulatif = get_object_or_404(RecapitulatifMensuelBailleur, pk=recapitulatif_id)
    
    try:
        # Utiliser le service pour générer le reçu GESTIMMOB
        from .services_recus import generer_recu_gestimmob_automatique
        
        recu = generer_recu_gestimmob_automatique(recapitulatif, request.user)
        
        messages.success(request, f'Reçu GESTIMMOB créé avec succès: {recu.numero_recu}')
        return redirect('paiements:detail_recu_recapitulatif', pk=recu.pk)
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la création du reçu GESTIMMOB: {str(e)}')
        logger.error(f"Erreur création reçu GESTIMMOB: {str(e)}")
        return redirect('paiements:detail_recapitulatif', recapitulatif_id=recapitulatif_id)


@login_required
def apercu_recu_recapitulatif(request, pk):
    """Aperçu d'un reçu de récapitulatif."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus_recapitulatifs')
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    # Calculer les totaux
    totaux = recu.recapitulatif.calculer_totaux_bailleur()
    
    context = {
        'page_title': f'Aperçu - Reçu {recu.numero_recu}',
        'page_icon': 'eye',
        'recu': recu,
        'totaux': totaux,
        'apercu': True,
    }
    
    return render(request, 'paiements/recus/apercu_recu_recapitulatif.html', context)


@login_required
@require_http_methods(["POST"])
def marquer_recu_envoye(request, pk):
    """Marquer un reçu comme envoyé."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        return JsonResponse({'success': False, 'message': permissions['message']})
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    try:
        mode_envoi = request.POST.get('mode_envoi', 'email')
        recu.marquer_envoye(mode_envoi)
        
        return JsonResponse({
            'success': True,
            'message': f'Reçu marqué comme envoyé par {recu.get_mode_envoi_display()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def valider_recu_recapitulatif(request, pk):
    """Valider un reçu de récapitulatif."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        return JsonResponse({'success': False, 'message': permissions['message']})
    
    recu = get_object_or_404(RecuRecapitulatif, pk=pk)
    
    try:
        recu.statut = 'valide'
        recu.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Reçu validé avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@login_required
def statistiques_recus_recapitulatifs(request):
    """Statistiques des reçus de récapitulatifs."""
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Statistiques générales
    stats_generales = {
        'total_recus': RecuRecapitulatif.objects.count(),
        'recus_imprimes': RecuRecapitulatif.objects.filter(imprime=True).count(),
        'recus_envoyes': RecuRecapitulatif.objects.filter(envoye=True).count(),
        'recus_valides': RecuRecapitulatif.objects.filter(statut='valide').count(),
    }
    
    # Statistiques par statut
    stats_statut = RecuRecapitulatif.objects.values('statut').annotate(
        count=Count('id')
    ).order_by('statut')
    
    # Statistiques par type
    stats_type = RecuRecapitulatif.objects.values('type_recu').annotate(
        count=Count('id')
    ).order_by('type_recu')
    
    # Statistiques par mois
    from django.db.models.functions import TruncMonth
    stats_mensuelles = RecuRecapitulatif.objects.annotate(
        mois=TruncMonth('date_creation')
    ).values('mois').annotate(
        count=Count('id')
    ).order_by('-mois')[:12]
    
    context = {
        'page_title': 'Statistiques des Reçus',
        'page_icon': 'bar-chart',
        'stats_generales': stats_generales,
        'stats_statut': stats_statut,
        'stats_type': stats_type,
        'stats_mensuelles': stats_mensuelles,
    }
    
    return render(request, 'paiements/recus/statistiques_recus_recapitulatifs.html', context)
