#!/usr/bin/env python
"""
Script de réparation des avances incohérentes
Corrige les montants restants basés sur les consommations réelles
"""

import os
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models_avance import AvanceLoyer, ConsommationAvance

def reparer_avances_incoherentes():
    print("REPARATION DES AVANCES INCOHERENTES")
    print("=" * 40)
    
    avances = AvanceLoyer.objects.all()
    total_reparees = 0
    
    for avance in avances:
        print(f"\nAvance ID: {avance.id}")
        print(f"Contrat: {avance.contrat.numero_contrat}")
        print(f"Montant original: {avance.montant_avance} F CFA")
        print(f"Montant restant (DB): {avance.montant_restant} F CFA")
        
        # Calculer le montant réel consommé
        montant_consomme_reel = sum(
            float(c.montant_consomme) for c in ConsommationAvance.objects.filter(avance=avance)
        )
        
        # Calculer le montant restant correct
        montant_restant_correct = float(avance.montant_avance) - montant_consomme_reel
        
        print(f"Montant consomme (enregistrements): {montant_consomme_reel} F CFA")
        print(f"Montant restant (calcule): {montant_restant_correct} F CFA")
        
        # Vérifier s'il y a une incohérence
        difference = abs(float(avance.montant_restant) - montant_restant_correct)
        
        if difference > 0.01:  # Tolérance de 1 centime
            print(f"INCOHERENCE DETECTEE: {difference} F CFA")
            
            # Corriger le montant restant
            avance.montant_restant = Decimal(str(montant_restant_correct))
            
            # Mettre à jour le statut
            if avance.montant_restant <= 0:
                avance.statut = 'epuisee'
                avance.montant_restant = Decimal('0')
            else:
                avance.statut = 'active'
            
            avance.save()
            print(f"CORRIGE: Montant restant = {avance.montant_restant} F CFA, Statut = {avance.statut}")
            total_reparees += 1
        else:
            print("COHERENT: Aucune correction necessaire")
    
    print(f"\nREPARATION TERMINEE: {total_reparees} avances corrigees")

if __name__ == "__main__":
    try:
        reparer_avances_incoherentes()
    except Exception as e:
        print(f"ERREUR lors de la reparation: {str(e)}")
        import traceback
        traceback.print_exc()
