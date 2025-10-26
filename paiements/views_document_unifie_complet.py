"""
Vues unifiées pour la génération de TOUS les documents A5
- Paiements (récépissés, quittances, avances, cautions)
- Retraits bailleurs (quittances de retrait)
- Récapitulatifs (quittances de récapitulatif)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from .models import Paiement
from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
import logging

logger = logging.getLogger(__name__)


# ===== DOCUMENTS DE PAIEMENTS =====

@login_required
@require_http_methods(["GET"])
def generer_recu_paiement_a5(request, paiement_id):
    """Génère un récépissé de paiement A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_recu', user=request.user, paiement_id=paiement_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du récépissé: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_quittance_paiement_a5(request, paiement_id):
    """Génère une quittance de paiement A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_quittance', user=request.user, paiement_id=paiement_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération de la quittance: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_avance_paiement_a5(request, paiement_id):
    """Génère un récépissé d'avance A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_avance', user=request.user, paiement_id=paiement_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du récépissé d'avance: {str(e)}")
        return redirect('paiements:liste')


@login_required
@require_http_methods(["GET"])
def generer_caution_paiement_a5(request, paiement_id):
    """Génère un récépissé de caution A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_caution', user=request.user, paiement_id=paiement_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du récépissé de caution: {str(e)}")
        return redirect('paiements:liste')


# ===== DOCUMENTS DE RETRAITS =====

@login_required
@require_http_methods(["GET"])
def generer_quittance_retrait_a5(request, retrait_id):
    """Génère une quittance de retrait A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('retrait_quittance', user=request.user, retrait_id=retrait_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération de la quittance de retrait: {str(e)}")
        return redirect('paiements:retraits_liste')


@login_required
@require_http_methods(["GET"])
def generer_recu_retrait_a5(request, retrait_id):
    """Génère un récépissé de retrait A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('retrait_recu', retrait_id=retrait_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du récépissé de retrait: {str(e)}")
        return redirect('paiements:retraits_liste')


# ===== DOCUMENTS DE RÉCAPITULATIFS =====

@login_required
@require_http_methods(["GET"])
def generer_quittance_recap_a5(request, recapitulatif_id):
    """Génère une quittance de récapitulatif A5."""
    try:
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('recap_quittance', user=request.user, recapitulatif_id=recapitulatif_id)
        return HttpResponse(html_content, content_type='text/html')
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération de la quittance de récapitulatif: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels')


# ===== VUE GÉNÉRIQUE =====

@login_required
@require_http_methods(["GET"])
def generer_document_generique_a5(request, document_type, object_id):
    """
    Vue générique pour générer n'importe quel document A5.
    
    Args:
        document_type: Type de document (paiement_recu, paiement_quittance, etc.)
        object_id: ID de l'objet (paiement, retrait, récapitulatif)
    """
    try:
        service = DocumentUnifieA5ServiceComplet()
        
        # Déterminer les paramètres selon le type
        if document_type.startswith('paiement_'):
            html_content = service.generer_document_unifie(document_type, paiement_id=object_id)
        elif document_type == 'retrait_quittance':
            html_content = service.generer_document_unifie(document_type, retrait_id=object_id)
        elif document_type == 'recap_quittance':
            html_content = service.generer_document_unifie(document_type, recapitulatif_id=object_id)
        else:
            raise ValueError(f"Type de document non supporté: {document_type}")
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du document: {str(e)}")
        return redirect('paiements:liste')

