#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from paiements.models_avance import AvanceLoyer
from paiements.services_document_unifie_complet import DocumentUnifieA5ServiceComplet

# Test de l'avance liée au paiement 2
avance = AvanceLoyer.objects.filter(paiement_id=2).first()
print('Avance trouvée:', avance)
if avance:
    print('Nombre mois couverts:', avance.nombre_mois_couverts)
    print('Mois début:', avance.mois_debut_couverture)
    print('Mois fin:', avance.mois_fin_couverture)
    print('Montant avance:', avance.montant_avance)
    print('Loyer mensuel:', avance.contrat.loyer_mensuel)
    
    # Test de la méthode get_mois_couverts_liste
    if hasattr(avance, 'get_mois_couverts_liste'):
        print('Méthode get_mois_couverts_liste existe')
        try:
            mois_liste = avance.get_mois_couverts_liste()
            print('Mois liste:', mois_liste)
        except Exception as e:
            print('Erreur get_mois_couverts_liste:', e)
    else:
        print('Méthode get_mois_couverts_liste n\'existe pas')

# Test du service de génération
print('\n=== TEST SERVICE ===')
service = DocumentUnifieA5ServiceComplet()
context = service._prepare_paiement_context('paiement_avance', 2)
print('Montant total:', context.get('montant_total'))
print('Mois couverts:', context.get('mois_couverts'))
print('Avance loyer:', context.get('avance_loyer'))
