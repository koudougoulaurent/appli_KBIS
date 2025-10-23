#!/usr/bin/env python
"""
Vues pour la génération de PDF de contrats avec templates mis à jour
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from core.utils import check_group_permissions
from .models import Contrat
from .services import ContratPDFService
import logging

logger = logging.getLogger(__name__)


@login_required
def generer_contrat_pdf_updated(request, pk):
    """
    Vue pour générer le PDF d'un contrat avec le template mis à jour
    """
    # Vérification des permissions simplifiée pour les superutilisateurs
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Accès refusé. Permissions insuffisantes.')
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Remplir automatiquement les champs manquants
        service = ContratPDFService(contrat)
        contrat = service.auto_remplir_champs_contrat()
        
        # Générer le PDF du contrat
        pdf_buffer = service.generate_contrat_pdf()
        
        # Créer la réponse HTTP avec le PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contrat_{contrat.numero_contrat}_updated.pdf"'
        
        messages.success(request, f'PDF du contrat {contrat.numero_contrat} généré avec succès!')
        return response
        
    except Exception as e:
        logger.error(f'Erreur lors de la génération du PDF du contrat {pk}: {str(e)}')
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('contrats:detail', pk=pk)


@login_required
def generer_etat_lieux_pdf(request, pk):
    """
    Vue pour générer le PDF d'un état des lieux
    """
    # Vérification des permissions simplifiée pour les superutilisateurs
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Accès refusé. Permissions insuffisantes.')
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Générer le PDF de l'état des lieux
        service = ContratPDFService(contrat)
        pdf_buffer = service.generate_etat_lieux_pdf()
        
        # Créer la réponse HTTP avec le PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="etat_lieux_{contrat.numero_contrat}.pdf"'
        
        messages.success(request, f'PDF de l\'état des lieux du contrat {contrat.numero_contrat} généré avec succès!')
        return response
        
    except Exception as e:
        logger.error(f'Erreur lors de la génération du PDF état des lieux {pk}: {str(e)}')
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('contrats:detail', pk=pk)


@login_required
def generer_garantie_pdf(request, pk):
    """
    Vue pour générer le PDF d'une garantie
    """
    # Vérification des permissions simplifiée pour les superutilisateurs
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Accès refusé. Permissions insuffisantes.')
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Remplir automatiquement les champs manquants
        service = ContratPDFService(contrat)
        contrat = service.auto_remplir_champs_contrat()
        
        # Générer le PDF de la garantie
        pdf_buffer = service.generate_garantie_pdf()
        
        # Créer la réponse HTTP avec le PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="garantie_{contrat.numero_contrat}.pdf"'
        
        messages.success(request, f'PDF de la garantie du contrat {contrat.numero_contrat} généré avec succès!')
        return response
        
    except Exception as e:
        logger.error(f'Erreur lors de la génération du PDF garantie {pk}: {str(e)}')
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('contrats:detail', pk=pk)


@login_required
def generer_documents_complets(request, pk):
    """
    Vue pour générer tous les documents d'un contrat (contrat + état des lieux + garantie)
    """
    # Vérification des permissions simplifiée pour les superutilisateurs
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Accès refusé. Permissions insuffisantes.')
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Remplir automatiquement les champs manquants
        service = ContratPDFService(contrat)
        contrat = service.auto_remplir_champs_contrat()
        
        # Générer tous les PDF
        contrat_pdf = service.generate_contrat_pdf()
        etat_lieux_pdf = service.generate_etat_lieux_pdf()
        garantie_pdf = service.generate_garantie_pdf()
        
        # Combiner les PDF (optionnel - pour l'instant on retourne le contrat principal)
        response = HttpResponse(contrat_pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="documents_complets_{contrat.numero_contrat}.pdf"'
        
        messages.success(request, f'Documents complets du contrat {contrat.numero_contrat} générés avec succès!')
        return response
        
    except Exception as e:
        logger.error(f'Erreur lors de la génération des documents complets {pk}: {str(e)}')
        messages.error(request, f'Erreur lors de la génération des documents: {str(e)}')
        return redirect('contrats:detail', pk=pk)


@login_required
def auto_remplir_contrat(request, pk):
    """
    Vue pour remplir automatiquement les champs d'un contrat
    """
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Remplir automatiquement les champs
        service = ContratPDFService(contrat)
        contrat = service.auto_remplir_champs_contrat()
        
        messages.success(request, f'Champs du contrat {contrat.numero_contrat} remplis automatiquement!')
        return redirect('contrats:detail', pk=pk)
        
    except Exception as e:
        logger.error(f'Erreur lors du remplissage automatique du contrat {pk}: {str(e)}')
        messages.error(request, f'Erreur lors du remplissage automatique: {str(e)}')
        return redirect('contrats:detail', pk=pk)

