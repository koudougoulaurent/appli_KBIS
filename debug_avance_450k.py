#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from paiements.models_avance import AvanceLoyer
from paiements.models import Paiement

# Chercher l'avance de 450,000 F CFA
print("=== RECHERCHE AVANCE 450,000 F CFA ===")
avance_450k = AvanceLoyer.objects.filter(montant_avance=450000).first()
print('Avance 450k:', avance_450k)

if avance_450k:
    print('Paiement lié:', avance_450k.paiement)
    print('Contrat:', avance_450k.contrat.id)
    print('Loyer mensuel:', avance_450k.contrat.loyer_mensuel)
    print('Montant avance:', avance_450k.montant_avance)
    print('Nombre mois couverts:', avance_450k.nombre_mois_couverts)
    
    # Chercher le paiement correspondant
    if avance_450k.paiement:
        paiement = avance_450k.paiement
        print('\n=== PAIEMENT LIÉ ===')
        print('ID paiement:', paiement.id)
        print('Montant paiement:', paiement.montant)
        print('Type paiement:', paiement.type_paiement)
        print('Date paiement:', paiement.date_paiement)
        
        # Tester le service de génération
        print('\n=== TEST SERVICE GÉNÉRATION ===')
        from paiements.services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        service = DocumentUnifieA5ServiceComplet()
        context = service._prepare_paiement_context('paiement_avance', paiement.id)
        print('Montant total dans le contexte:', context.get('montant_total'))
        print('Mois couverts:', context.get('mois_couverts'))
        print('Avance loyer:', context.get('avance_loyer'))
else:
    print("Aucune avance de 450,000 F CFA trouvée")
    
    # Lister toutes les avances
    print('\n=== TOUTES LES AVANCES ===')
    avances = AvanceLoyer.objects.all()[:10]
    for avance in avances:
        print(f'Avance {avance.id}: {avance.montant_avance} F CFA, Contrat: {avance.contrat.id}, Paiement: {avance.paiement.id if avance.paiement else None}')
