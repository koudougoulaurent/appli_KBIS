"""
Vue de test pour les documents de paiement avec template KBIS
"""
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from paiements.models import Paiement


@login_required
def test_recu_kbis(request, paiement_id):
    """Génère un reçu de paiement avec le template KBIS."""
    
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Utiliser la nouvelle méthode KBIS pour générer le document
        document_html = paiement.generer_document_kbis('recu')
        
        if document_html:
            return HttpResponse(document_html)
        else:
            messages.error(request, "Erreur lors de la génération du document KBIS")
            return render(request, 'error.html')
            
    except Exception as e:
        messages.error(request, f"Erreur: {e}")
        return render(request, 'error.html')


@login_required
def test_facture_kbis(request, paiement_id):
    """Génère une facture avec le template KBIS."""
    
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        # Utiliser la nouvelle méthode KBIS pour générer une facture
        document_html = paiement.generer_document_kbis('facture')
        
        if document_html:
            return HttpResponse(document_html)
        else:
            messages.error(request, "Erreur lors de la génération de la facture KBIS")
            return render(request, 'error.html')
            
    except Exception as e:
        messages.error(request, f"Erreur: {e}")
        return render(request, 'error.html')