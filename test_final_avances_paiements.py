#!/usr/bin/env python
"""
Test final complet de l'intégration avances-paiements
Validation de tous les scénarios critiques
"""

import os
import django
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models_avance import AvanceLoyer, ConsommationAvance
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat

def test_final_avances_paiements():
    print("TEST FINAL COMPLET - INTEGRATION AVANCES-PAIEMENTS")
    print("=" * 60)
    
    # Récupérer tous les contrats avec avances
    contrats_avec_avances = Contrat.objects.filter(avances_loyer__isnull=False).distinct()
    
    print(f"Nombre de contrats avec avances: {contrats_avec_avances.count()}")
    print()
    
    total_tests = 0
    tests_reussis = 0
    
    for contrat in contrats_avec_avances:
        print(f"CONTRAT: {contrat.numero_contrat}")
        print(f"Locataire: {contrat.locataire.get_nom_complet()}")
        print(f"Loyer mensuel: {contrat.loyer_mensuel} F CFA")
        print("-" * 40)
        
        # Récupérer les avances de ce contrat
        avances = contrat.avances_loyer.all()
        
        for avance in avances:
            print(f"  AVANCE ID: {avance.id}")
            print(f"  Montant: {avance.montant_avance} F CFA")
            print(f"  Mois couverts: {avance.nombre_mois_couverts}")
            print(f"  Date début: {avance.mois_debut_couverture}")
            print(f"  Date fin: {avance.mois_fin_couverture}")
            print(f"  Montant restant: {avance.montant_restant} F CFA")
            print(f"  Statut: {avance.statut}")
            
            # Test 1: Synchronisation des consommations
            total_tests += 1
            try:
                ServiceGestionAvance.synchroniser_consommations_manquantes(contrat)
                print("  OK - Synchronisation: OK")
                tests_reussis += 1
            except Exception as e:
                print(f"  ERREUR - Synchronisation: ERREUR - {str(e)}")
            
            # Test 2: Calcul du montant dû pour le premier mois
            total_tests += 1
            try:
                premier_mois = avance.mois_debut_couverture
                montant_du, montant_avance = ServiceGestionAvance.calculer_montant_du_mois(contrat, premier_mois)
                print(f"  OK - Calcul montant du ({premier_mois.strftime('%B %Y')}): {montant_du} F CFA (avance: {montant_avance} F CFA)")
                tests_reussis += 1
            except Exception as e:
                print(f"  ERREUR - Calcul montant du: ERREUR - {str(e)}")
            
            # Test 3: Vérification de la cohérence des montants
            total_tests += 1
            try:
                montant_consomme_calcule = sum(
                    float(c.montant_consomme) for c in ConsommationAvance.objects.filter(avance=avance)
                )
                montant_restant_calcule = float(avance.montant_avance) - montant_consomme_calcule
                
                if abs(float(avance.montant_restant) - montant_restant_calcule) < 0.01:
                    print("  OK - Coherence des montants: OK")
                    tests_reussis += 1
                else:
                    print(f"  ERREUR - Coherence des montants: INCOHERENT (DB: {avance.montant_restant}, Calcule: {montant_restant_calcule})")
            except Exception as e:
                print(f"  ERREUR - Coherence des montants: ERREUR - {str(e)}")
            
            # Test 4: Vérification des consommations
            total_tests += 1
            try:
                consommations = ConsommationAvance.objects.filter(avance=avance)
                print(f"  OK - Consommations: {consommations.count()} mois consommes")
                
                for consommation in consommations:
                    print(f"    - {consommation.mois_consomme.strftime('%B %Y')}: {consommation.montant_consomme} F CFA")
                
                tests_reussis += 1
            except Exception as e:
                print(f"  ERREUR - Consommations: ERREUR - {str(e)}")
            
            print()
    
    # Test global: Synchronisation de toutes les avances
    print("TEST GLOBAL - SYNCHRONISATION DE TOUTES LES AVANCES")
    print("-" * 50)
    
    total_tests += 1
    try:
        resultat = ServiceGestionAvance.synchroniser_toutes_avances()
        print(f"OK - Synchronisation globale: {resultat['message']}")
        tests_reussis += 1
    except Exception as e:
        print(f"ERREUR - Synchronisation globale: ERREUR - {str(e)}")
    
    # Résumé final
    print()
    print("RESUME FINAL")
    print("=" * 20)
    print(f"Tests totaux: {total_tests}")
    print(f"Tests réussis: {tests_reussis}")
    print(f"Tests échoués: {total_tests - tests_reussis}")
    print(f"Taux de réussite: {(tests_reussis / total_tests * 100):.1f}%")
    
    if tests_reussis == total_tests:
        print("OK - TOUS LES TESTS SONT PASSES - SYSTEME VALIDE")
    else:
        print("ERREUR - CERTAINS TESTS ONT ECHOUE - VERIFICATION NECESSAIRE")
    
    print()
    print("TEST FINAL TERMINE")

if __name__ == "__main__":
    try:
        test_final_avances_paiements()
    except Exception as e:
        print(f"ERREUR lors du test final: {str(e)}")
        import traceback
        traceback.print_exc()
