#!/usr/bin/env python
"""
Script pour convertir tous les paiements d'avance en AvanceLoyer actifs
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from paiements.services_avance import ServiceGestionAvance
from decimal import Decimal

def convertir_paiements_avance():
    """Convertit tous les paiements d'avance en AvanceLoyer actifs"""
    
    print("Recherche des paiements d'avance a convertir...")
    
    # Trouver tous les paiements d'avance
    paiements_avance = Paiement.objects.filter(
        type_paiement__in=['avance_loyer', 'avance'],
        statut='valide'
    )
    
    print(f"Trouve {paiements_avance.count()} paiements d'avance a convertir")
    
    for paiement in paiements_avance:
        try:
            print(f"\nConversion du paiement {paiement.id}...")
            print(f"   Contrat: {paiement.contrat.numero_contrat}")
            print(f"   Montant: {paiement.montant} F CFA")
            print(f"   Date: {paiement.date_paiement}")
            
            # Vérifier si un AvanceLoyer existe déjà pour ce paiement
            avance_existant = AvanceLoyer.objects.filter(
                contrat=paiement.contrat,
                montant_avance=paiement.montant,
                date_avance=paiement.date_paiement
            ).first()
            
            if avance_existant:
                print(f"   AvanceLoyer deja existant: {avance_existant.id}")
                # Mettre à jour le statut si nécessaire
                if avance_existant.statut != 'active':
                    avance_existant.statut = 'active'
                    avance_existant.montant_restant = avance_existant.montant_avance
                    avance_existant.save()
                    print(f"   Statut mis a jour: {avance_existant.statut}")
                continue
            
            # Créer un nouvel AvanceLoyer
            avance = ServiceGestionAvance.creer_avance_loyer(
                contrat=paiement.contrat,
                montant_avance=Decimal(str(paiement.montant)),
                date_avance=paiement.date_paiement,
                notes=f"Converti depuis paiement {paiement.id}"
            )
            
            print(f"   AvanceLoyer cree: {avance.id}")
            print(f"   Mois couverts: {avance.nombre_mois_couverts}")
            print(f"   Montant restant: {avance.montant_restant}")
            print(f"   Statut: {avance.statut}")
            
        except Exception as e:
            print(f"   Erreur lors de la conversion: {str(e)}")
            continue
    
    print(f"\nConversion terminee !")
    
    # Afficher le résumé des avances actives
    avances_actives = AvanceLoyer.objects.filter(statut='active')
    print(f"\nResume des avances actives:")
    print(f"   Total: {avances_actives.count()}")
    
    for avance in avances_actives:
        print(f"   - Contrat {avance.contrat.numero_contrat}: {avance.montant_avance} F CFA ({avance.nombre_mois_couverts} mois)")

if __name__ == "__main__":
    convertir_paiements_avance()
