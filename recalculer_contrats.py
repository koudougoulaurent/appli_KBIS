#!/usr/bin/env python
"""
Script pour recalculer les valeurs de tous les contrats
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packages.hotspot.settings_dev')
django.setup()

from contrats.models import Contrat
from contrats.services_contrat_pdf_updated import ContratPDFServiceUpdated

def recalculer_contrats():
    """Recalcule les valeurs de tous les contrats actifs"""
    contrats = Contrat.objects.filter(est_actif=True)
    
    print(f"\n{'='*80}")
    print(f"RECALCUL DES VALEURS POUR {contrats.count()} CONTRATS ACTIFS")
    print(f"{'='*80}\n")
    
    for contrat in contrats:
        print(f"Contrat #{contrat.id} - {contrat.numero_contrat}")
        print(f"  Loyer: {contrat.loyer_mensuel} FCFA")
        print(f"  Caution: {contrat.depot_garantie} FCFA")
        print(f"  Avance: {contrat.avance_loyer} FCFA")
        print(f"  AVANT - Nombre mois caution: |{contrat.nombre_mois_caution}|")
        print(f"  AVANT - Mois début paiement: |{contrat.mois_debut_paiement}|")
        
        try:
            service = ContratPDFServiceUpdated(contrat)
            service.auto_remplir_champs_contrat()
            contrat.refresh_from_db()
            
            print(f"  APRÈS - Nombre mois caution: |{contrat.nombre_mois_caution}|")
            print(f"  APRÈS - Mois début paiement: |{contrat.mois_debut_paiement}|")
            print(f"  ✅ Recalculé avec succès\n")
        except Exception as e:
            print(f"  ❌ Erreur: {e}\n")

if __name__ == '__main__':
    recalculer_contrats()
    print(f"\n{'='*80}")
    print("RECALCUL TERMINÉ")
    print(f"{'='*80}\n")
