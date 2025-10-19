#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from paiements.models_avance import AvanceLoyer
from paiements.models import Paiement
from core.id_generator import IDGenerator

# Récupérer l'avance de 450,000 F CFA
avance_450k = AvanceLoyer.objects.filter(montant_avance=450000).first()

if avance_450k:
    print(f"Avance trouvée: {avance_450k}")
    print(f"Contrat: {avance_450k.contrat.id}")
    print(f"Locataire: {avance_450k.contrat.locataire.get_nom_complet()}")
    print(f"Montant: {avance_450k.montant_avance} F CFA")
    print(f"Date avance: {avance_450k.date_avance}")
    
    # Créer un paiement d'avance correspondant
    numero_paiement = IDGenerator.generate_id('paiement', date_paiement=avance_450k.date_avance)
    
    paiement = Paiement.objects.create(
        contrat=avance_450k.contrat,
        montant=avance_450k.montant_avance,
        date_paiement=avance_450k.date_avance,
        type_paiement='avance',
        statut='valide',
        numero_paiement=numero_paiement,
        notes=f"Paiement d'avance automatique - {avance_450k.nombre_mois_couverts} mois couverts"
    )
    
    print(f"\nPaiement créé: {paiement.id}")
    print(f"Numéro: {paiement.numero_paiement}")
    print(f"Montant: {paiement.montant} F CFA")
    
    # Lier l'avance au paiement
    avance_450k.paiement = paiement
    avance_450k.save()
    
    print(f"\nAvance liée au paiement {paiement.id}")
    
    # Tester le service de génération
    print("\n=== TEST SERVICE GÉNÉRATION ===")
    from paiements.services_document_unifie_complet import DocumentUnifieA5ServiceComplet
    service = DocumentUnifieA5ServiceComplet()
    context = service._prepare_paiement_context('paiement_avance', paiement.id)
    print('Montant total dans le contexte:', context.get('montant_total'))
    print('Mois couverts:', context.get('mois_couverts'))
    
else:
    print("Aucune avance de 450,000 F CFA trouvée")
