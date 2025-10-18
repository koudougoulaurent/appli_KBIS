"""
Vues pour la génération de documents unifiés A5
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from .models import Paiement
from .services_document_unifie import DocumentUnifieA5Service, DocumentUnifieA5ViewMixin
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def generer_recu_unifie_a5(request, paiement_id):
    """
    Génère un récépissé unifié au format A5 - VERSION SIMPLE.
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Générer le document directement
        service = DocumentUnifieA5Service()
        html_content = service.generer_recu_unifie(paiement_id, 'recu')
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        # En cas d'erreur, rediriger vers la liste avec un message
        messages.error(request, f"Erreur lors de la génération du document: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_quittance_unifie_a5(request, paiement_id):
    """
    Génère une quittance unifiée au format A5 - VERSION SIMPLE.
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Générer le document directement
        service = DocumentUnifieA5Service()
        html_content = service.generer_recu_unifie(paiement_id, 'quittance')
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        # En cas d'erreur, rediriger vers la liste avec un message
        messages.error(request, f"Erreur lors de la génération du document: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_avance_unifie_a5(request, paiement_id):
    """
    Génère un récépissé d'avance unifié au format A5 - VERSION SIMPLE.
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Générer le document directement
        service = DocumentUnifieA5Service()
        html_content = service.generer_recu_unifie(paiement_id, 'avance')
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        # En cas d'erreur, rediriger vers la liste avec un message
        messages.error(request, f"Erreur lors de la génération du document: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_caution_unifie_a5(request, paiement_id):
    """
    Génère un récépissé de caution unifié au format A5 - VERSION SIMPLE.
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Générer le document directement
        service = DocumentUnifieA5Service()
        html_content = service.generer_recu_unifie(paiement_id, 'caution')
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        # En cas d'erreur, rediriger vers la liste avec un message
        messages.error(request, f"Erreur lors de la génération du document: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_document_unifie_a5(request, paiement_id, document_type):
    """
    Génère un document unifié A5 selon le type spécifié.
    
    Args:
        paiement_id (int): ID du paiement
        document_type (str): Type de document ('recu', 'quittance', 'avance', 'caution')
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Vérifier que l'utilisateur est connecté (permission de base)
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour accéder à cette fonctionnalité.")
            return redirect('paiements:liste')
        
        # Valider le type de document
        valid_types = ['recu', 'quittance', 'avance', 'caution']
        if document_type not in valid_types:
            messages.error(request, f"Type de document invalide: {document_type}")
            return redirect('paiements:liste')
        
        # Générer le document
        service = DocumentUnifieA5Service()
        html_content = service.generer_recu_unifie(paiement_id, document_type)
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du document unifié A5: {str(e)}")
        messages.error(request, f"Erreur lors de la génération du document: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def preview_document_unifie_a5(request, paiement_id, document_type):
    """
    Aperçu d'un document unifié A5 sans impression automatique.
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Vérifier que l'utilisateur est connecté (permission de base)
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour accéder à cette fonctionnalité.")
            return redirect('paiements:liste')
        
        # Valider le type de document
        valid_types = ['recu', 'quittance', 'avance', 'caution']
        if document_type not in valid_types:
            messages.error(request, f"Type de document invalide: {document_type}")
            return redirect('paiements:liste')
        
        # Générer le document
        service = DocumentUnifieA5Service()
        html_content = service.generer_recu_unifie(paiement_id, document_type)
        
        # Retirer le script d'impression automatique pour l'aperçu
        html_content = html_content.replace(
            'setTimeout(function() { window.print(); }, 1000);',
            '// Impression désactivée pour l\'aperçu'
        )
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'aperçu du document unifié A5: {str(e)}")
        messages.error(request, f"Erreur lors de l'aperçu du document: {str(e)}")
        return redirect('paiements:liste')


