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

print("=== LIAISON DE TOUTES LES AVANCES SANS PAIEMENT ===")

# Récupérer toutes les avances sans paiement
avances_sans_paiement = AvanceLoyer.objects.filter(paiement__isnull=True)
print(f"Avances sans paiement trouvées: {avances_sans_paiement.count()}")

liaisons_effectuees = 0

for avance in avances_sans_paiement:
    print(f"\n--- Avance {avance.id}: {avance.montant_avance} F CFA ---")
    print(f"Contrat: {avance.contrat.id}")
    print(f"Locataire: {avance.contrat.locataire.get_nom_complet()}")
    print(f"Date avance: {avance.date_avance}")
    print(f"Mois couverts: {avance.nombre_mois_couverts}")
    
    # Créer un paiement d'avance correspondant
    numero_paiement = IDGenerator.generate_id('paiement', date_paiement=avance.date_avance)
    
    try:
        paiement = Paiement.objects.create(
            contrat=avance.contrat,
            montant=avance.montant_avance,
            date_paiement=avance.date_avance,
            type_paiement='avance',
            statut='valide',
            numero_paiement=numero_paiement,
            notes=f"Paiement d'avance automatique - {avance.nombre_mois_couverts} mois couverts"
        )
        
        print(f"[OK] Paiement créé: {paiement.id} ({paiement.numero_paiement})")
        
        # Lier l'avance au paiement
        avance.paiement = paiement
        avance.save()
        
        print(f"[OK] Avance liée au paiement {paiement.id}")
        liaisons_effectuees += 1
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la création du paiement: {e}")

print(f"\n=== RÉSUMÉ ===")
print(f"Liaisons effectuées: {liaisons_effectuees}")
print(f"Avances traitées: {avances_sans_paiement.count()}")

# Vérifier qu'il ne reste plus d'avances sans paiement
avances_restantes = AvanceLoyer.objects.filter(paiement__isnull=True).count()
print(f"Avances sans paiement restantes: {avances_restantes}")

if avances_restantes == 0:
    print("[SUCCESS] Toutes les avances sont maintenant liées à des paiements !")
else:
    print("[WARNING] Il reste des avances sans paiement")
