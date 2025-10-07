#!/usr/bin/env python
"""
Test de validation de la progression corrigée
"""

import os
import django
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models_avance import AvanceLoyer, ConsommationAvance
from paiements.services_monitoring_avance import ServiceMonitoringAvance

def test_validation_progression_corrigee():
    print("VALIDATION DE LA PROGRESSION CORRIGEE")
    print("=" * 45)
    
    # Récupérer toutes les avances
    avances = AvanceLoyer.objects.all()
    
    for avance in avances:
        print(f"\nAVANCE ID: {avance.id}")
        print(f"Contrat: {avance.contrat.numero_contrat}")
        print(f"Locataire: {avance.contrat.locataire.get_nom_complet()}")
        print(f"Montant avance: {avance.montant_avance} F CFA")
        print(f"Loyer mensuel: {avance.loyer_mensuel} F CFA")
        print(f"Mois couverts: {avance.nombre_mois_couverts}")
        print(f"Montant restant: {avance.montant_restant} F CFA")
        print(f"Statut: {avance.statut}")
        
        # Consommations enregistrées
        consommations = ConsommationAvance.objects.filter(avance=avance)
        print(f"Consommations enregistrées: {consommations.count()}")
        
        for c in consommations:
            print(f"  - {c.mois_consomme.strftime('%B %Y')}: {c.montant_consomme} F CFA")
        
        # Analyse de progression
        progression = ServiceMonitoringAvance.analyser_progression_avance(avance)
        
        if 'erreur' in progression:
            print(f"ERREUR: {progression['erreur']}")
        else:
            print(f"Progression: {progression['progression']}%")
            print(f"Pourcentage réel: {progression['pourcentage_reel']}%")
            print(f"Montant réel consommé: {progression['montant_reel_consomme']} F CFA")
            print(f"Mois consommés: {progression['mois_consommes']}")
            print(f"Statut progression: {progression['statut_progression']}")
            
            # Vérification de cohérence
            montant_consomme_calcule = sum(float(c.montant_consomme) for c in consommations)
            pourcentage_calcule = (montant_consomme_calcule / float(avance.montant_avance) * 100) if avance.montant_avance > 0 else 0
            
            print(f"Vérification - Montant consommé: {montant_consomme_calcule} F CFA")
            print(f"Vérification - Pourcentage: {pourcentage_calcule:.1f}%")
            
            # Vérifier la cohérence
            if abs(progression['pourcentage_reel'] - pourcentage_calcule) < 0.01:
                print("OK - COHERENT")
            else:
                print("ERREUR - INCOHERENT")
        
        print("-" * 50)
    
    print("\nVALIDATION TERMINEE")

if __name__ == "__main__":
    try:
        test_validation_progression_corrigee()
    except Exception as e:
        print(f"ERREUR lors de la validation: {str(e)}")
        import traceback
        traceback.print_exc()
