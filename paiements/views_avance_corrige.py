"""
Vues pour tester le système d'avances corrigé
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from paiements.services_avance_corrige import ServiceAvanceCorrige
from paiements.services_document_unifie_complet import DocumentUnifieA5ServiceComplet
from contrats.models import Contrat
import json


@login_required
def test_avance_corrige(request, paiement_id):
    """
    Teste le système d'avance corrigé pour un paiement spécifique.
    """
    try:
        paiement = get_object_or_404(Paiement, id=paiement_id)
        
        if paiement.type_paiement != 'avance':
            messages.error(request, "Ce paiement n'est pas une avance")
            return redirect('paiements:liste')
        
        # Utiliser le service corrigé
        donnees_avance = ServiceAvanceCorrige.generer_recu_avance_corrige(paiement_id)
        
        context = {
            'paiement': paiement,
            'donnees_avance': donnees_avance,
            'title': f'Test Avance Corrigée - Paiement {paiement_id}'
        }
        
        return render(request, 'paiements/test_avance_corrige.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du test: {str(e)}")
        return redirect('paiements:liste')


@login_required
def generer_recu_avance_corrige(request, paiement_id):
    """
    Génère un récépissé d'avance avec le système corrigé.
    """
    try:
        # Utiliser le service corrigé
        donnees_avance = ServiceAvanceCorrige.generer_recu_avance_corrige(paiement_id)
        
        # Générer le document avec les données corrigées
        service = DocumentUnifieA5ServiceComplet()
        
        # Préparer le contexte avec les données corrigées
        context = {
            'document_title': 'RÉCÉPISSÉ DE PAIEMENT D\'AVANCE',
            'document_type': 'paiement_avance',
            'generation_date': donnees_avance['paiement'].date_paiement,
            'config_entreprise': service.config_entreprise,
            
            # Informations du paiement
            'type_paiement': donnees_avance['paiement'].get_type_paiement_display(),
            'mode_paiement': donnees_avance['paiement'].get_mode_paiement_display(),
            'date_paiement': donnees_avance['paiement'].date_paiement,
            'numero_cheque': donnees_avance['paiement'].numero_cheque,
            'reference_virement': donnees_avance['paiement'].reference_virement,
            
            # Montants
            'montant_total': donnees_avance['montant_avance'],
            'montant_lettres': service._convertir_en_lettres(donnees_avance['montant_avance']),
            'montant_loyer': donnees_avance['loyer_mensuel'],
            'montant_charges_deduites': 0,
            'montant_net_paye': donnees_avance['montant_avance'],
            'montant_net_lettres': service._convertir_en_lettres(donnees_avance['montant_avance']),
            
            # Mois couverts corrigés
            'mois_couverts': donnees_avance['mois_couverts'],
            'mois_couverts_lettres': service._convertir_mois_couverts_en_lettres(donnees_avance['mois_couverts']),
            
            # Informations des entités
            'locataire': donnees_avance['paiement'].contrat.locataire,
            'propriete': donnees_avance['paiement'].contrat.propriete,
            'bailleur': donnees_avance['paiement'].contrat.propriete.bailleur,
            'contrat': donnees_avance['paiement'].contrat,
            'paiement': donnees_avance['paiement'],
            'avance_loyer': donnees_avance['avance'],
            'charges_deduites': [],
        }
        
        # Rendre le template
        from django.template.loader import render_to_string
        html_content = render_to_string('paiements/document_unifie_a5_complet.html', context)
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du récépissé: {str(e)}")
        return redirect('paiements:liste')


@login_required
def corriger_avance_ajax(request, avance_id):
    """
    Corrige une avance spécifique via AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        avance = get_object_or_404(AvanceLoyer, id=avance_id)
        
        # Calculer avec la logique corrigée
        mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
            avance.contrat, avance.montant_avance, avance.date_avance
        )
        
        if not mois_couverts_data:
            return JsonResponse({'error': 'Impossible de calculer les mois couverts'}, status=400)
        
        # Mettre à jour l'avance
        avance.nombre_mois_couverts = mois_couverts_data['nombre']
        avance.montant_reste = mois_couverts_data['reste']
        avance.mois_debut_couverture = mois_couverts_data['date_debut']
        avance.mois_fin_couverture = mois_couverts_data['date_fin']
        avance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Avance corrigée avec succès',
            'data': {
                'nombre_mois': mois_couverts_data['nombre'],
                'mois_texte': mois_couverts_data['mois_texte'],
                'date_debut': mois_couverts_data['date_debut'].strftime('%Y-%m-%d'),
                'date_fin': mois_couverts_data['date_fin'].strftime('%Y-%m-%d'),
                'reste': float(mois_couverts_data['reste'])
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def comparer_avances(request):
    """
    Compare les avances avant et après correction.
    """
    avances = AvanceLoyer.objects.filter(statut='active').select_related('contrat')[:10]
    
    comparaisons = []
    
    for avance in avances:
        try:
            # Calculer avec la logique corrigée
            mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                avance.contrat, avance.montant_avance, avance.date_avance
            )
            
            if mois_couverts_data:
                comparaison = {
                    'avance': avance,
                    'ancien': {
                        'nombre_mois': avance.nombre_mois_couverts,
                        'date_debut': avance.mois_debut_couverture,
                        'date_fin': avance.mois_fin_couverture,
                    },
                    'nouveau': {
                        'nombre_mois': mois_couverts_data['nombre'],
                        'date_debut': mois_couverts_data['date_debut'],
                        'date_fin': mois_couverts_data['date_fin'],
                        'mois_texte': mois_couverts_data['mois_texte'],
                    },
                    'changements': (
                        avance.nombre_mois_couverts != mois_couverts_data['nombre'] or
                        avance.mois_debut_couverture != mois_couverts_data['date_debut'] or
                        avance.mois_fin_couverture != mois_couverts_data['date_fin']
                    )
                }
                comparaisons.append(comparaison)
                
        except Exception as e:
            print(f"Erreur pour l'avance {avance.id}: {e}")
    
    context = {
        'comparaisons': comparaisons,
        'title': 'Comparaison des Avances - Avant/Après Correction'
    }
    
    return render(request, 'paiements/comparer_avances.html', context)
