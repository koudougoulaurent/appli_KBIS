#!/usr/bin/env python
"""
Test de la page de détail de progression avec une avance avancée
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
from contrats.models import Contrat

def test_detail_progression_avancee():
    print("TEST DE LA PAGE DE DETAIL DE PROGRESSION AVEC AVANCE AVANCEE")
    print("=" * 60)
    
    # Récupérer une avance pour tester
    avance = AvanceLoyer.objects.first()
    
    if not avance:
        print("Aucune avance trouvée pour le test")
        return
    
    print(f"Test avec l'avance ID: {avance.id}")
    print(f"Contrat: {avance.contrat.numero_contrat}")
    print(f"Locataire: {avance.contrat.locataire.get_nom_complet()}")
    print(f"Montant: {avance.montant_avance} F CFA")
    print(f"Loyer mensuel: {avance.loyer_mensuel} F CFA")
    print(f"Mois couverts: {avance.nombre_mois_couverts}")
    print(f"Date début couverture: {avance.mois_debut_couverture}")
    print(f"Date fin couverture: {avance.mois_fin_couverture}")
    print()
    
    # Simuler une avance qui a commencé il y a 3 mois
    print("SIMULATION: Avance commencée il y a 3 mois")
    print("-" * 40)
    
    # Modifier la date de début pour simuler une avance plus ancienne
    ancienne_date = date.today() - relativedelta(months=3)
    avance.mois_debut_couverture = ancienne_date.replace(day=1)
    avance.save()
    
    print(f"Nouvelle date de début: {avance.mois_debut_couverture}")
    print()
    
    # Test de l'analyse de progression
    print("1. ANALYSE DE PROGRESSION (après simulation):")
    progression = ServiceMonitoringAvance.analyser_progression_avance(avance)
    
    if 'erreur' in progression:
        print(f"   ERREUR: {progression['erreur']}")
    else:
        print(f"   Progression: {progression['progression']}%")
        print(f"   Mois consommés: {progression['mois_consommes']}")
        print(f"   Mois écoulés: {progression['mois_ecoules']}")
        print(f"   Mois restants: {progression['mois_restants_estimes']}")
        print(f"   Montant consommé: {progression['montant_reel_consomme']} F CFA")
        print(f"   Pourcentage réel: {progression['pourcentage_reel']}%")
        print(f"   Statut: {progression['statut_progression']}")
        if 'montant_devrait_etre_consomme' in progression:
            print(f"   Montant qui devrait être consommé: {progression['montant_devrait_etre_consomme']} F CFA")
    
    print()
    
    # Test de la liste des mois couverts
    print("2. LISTE DES MOIS COUVERTS:")
    mois_couverts = avance.get_mois_couverts_liste()
    print(f"   Nombre de mois: {len(mois_couverts)}")
    
    aujourd_hui = date.today()
    for i, mois in enumerate(mois_couverts):
        statut = "PASSÉ" if mois < aujourd_hui.replace(day=1) else "FUTUR" if mois > aujourd_hui.replace(day=1) else "EN COURS"
        print(f"   Mois {i+1}: {mois.strftime('%B %Y')} ({statut})")
    
    print()
    
    # Test de la simulation de consommation basée sur les mois écoulés
    print("3. SIMULATION DE CONSOMMATION:")
    aujourd_hui = datetime.now().date()
    
    if avance.mois_debut_couverture:
        mois_ecoules = ((aujourd_hui.year - avance.mois_debut_couverture.year) * 12 +
                       (aujourd_hui.month - avance.mois_debut_couverture.month))
        
        if aujourd_hui.day >= 15:
            mois_ecoules += 1
            
        print(f"   Mois écoulés depuis le début: {mois_ecoules}")
        print(f"   Montant qui devrait être consommé: {mois_ecoules * float(avance.loyer_mensuel)} F CFA")
        print(f"   Montant restant actuel: {avance.montant_restant} F CFA")
        
        # Calculer ce qui devrait être consommé
        montant_devrait_etre_consomme = min(mois_ecoules * float(avance.loyer_mensuel), float(avance.montant_avance))
        montant_restant_calcule = float(avance.montant_avance) - montant_devrait_etre_consomme
        
        print(f"   Montant restant calculé: {montant_restant_calcule} F CFA")
        print(f"   Différence: {float(avance.montant_restant) - montant_restant_calcule} F CFA")
        
        # Calculer le pourcentage de progression
        pourcentage_calcule = (montant_devrait_etre_consomme / float(avance.montant_avance) * 100)
        print(f"   Pourcentage calculé: {pourcentage_calcule:.1f}%")
    
    print()
    
    # Restaurer la date originale
    print("4. RESTAURATION DE LA DATE ORIGINALE:")
    avance.mois_debut_couverture = date(2025, 10, 1)
    avance.save()
    print(f"Date restaurée: {avance.mois_debut_couverture}")
    
    print()
    print("TEST TERMINE")

if __name__ == "__main__":
    try:
        test_detail_progression_avancee()
    except Exception as e:
        print(f"ERREUR lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
