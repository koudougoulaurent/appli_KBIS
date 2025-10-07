#!/usr/bin/env python
"""
Test de correction de la progression des avances
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

def test_correction_progression():
    print("TEST DE CORRECTION DE LA PROGRESSION")
    print("=" * 40)
    
    # Récupérer l'avance du contrat CTN0k5 (M laurenzo kdg)
    avance = AvanceLoyer.objects.filter(contrat__numero_contrat='CTN0k5').first()
    
    if not avance:
        print("Avance non trouvée")
        return
    
    print(f"Avance ID: {avance.id}")
    print(f"Contrat: {avance.contrat.numero_contrat}")
    print(f"Locataire: {avance.contrat.locataire.get_nom_complet()}")
    print(f"Montant avance: {avance.montant_avance} F CFA")
    print(f"Loyer mensuel: {avance.loyer_mensuel} F CFA")
    print(f"Mois couverts: {avance.nombre_mois_couverts}")
    print(f"Montant restant: {avance.montant_restant} F CFA")
    print()
    
    # Afficher les consommations existantes
    consommations = ConsommationAvance.objects.filter(avance=avance)
    print(f"Consommations enregistrées: {consommations.count()}")
    for c in consommations:
        print(f"  - {c.mois_consomme.strftime('%B %Y')}: {c.montant_consomme} F CFA")
    print()
    
    # Calculer le montant réel consommé
    montant_reel_consomme = sum(float(c.montant_consomme) for c in consommations)
    print(f"Montant réel consommé: {montant_reel_consomme} F CFA")
    
    # Calculer le pourcentage réel
    pourcentage_reel = (montant_reel_consomme / float(avance.montant_avance) * 100) if avance.montant_avance > 0 else 0
    print(f"Pourcentage réel: {pourcentage_reel:.1f}%")
    print()
    
    # Tester la méthode analyser_progression_avance
    print("ANALYSE DE PROGRESSION:")
    progression = ServiceMonitoringAvance.analyser_progression_avance(avance)
    
    if 'erreur' in progression:
        print(f"ERREUR: {progression['erreur']}")
    else:
        print(f"Progression: {progression['progression']}%")
        print(f"Pourcentage réel: {progression['pourcentage_reel']}%")
        print(f"Montant réel consommé: {progression['montant_reel_consomme']} F CFA")
        print(f"Mois consommés: {progression['mois_consommes']}")
        print(f"Statut: {progression['statut_progression']}")
    
    print()
    print("TEST TERMINE")

if __name__ == "__main__":
    try:
        test_correction_progression()
    except Exception as e:
        print(f"ERREUR lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
