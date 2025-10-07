#!/usr/bin/env python
"""
Test d'intégration des avances dans le système de paiements
Validation complète de la synchronisation automatique
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

def test_integration_avances_paiements():
    print("TEST D'INTEGRATION AVANCES - PAIEMENTS")
    print("=" * 50)
    
    # Récupérer un contrat avec avance
    contrat = Contrat.objects.filter(avances_loyer__isnull=False).first()
    
    if not contrat:
        print("Aucun contrat avec avance trouvé pour le test")
        return
    
    print(f"Test avec le contrat: {contrat.numero_contrat}")
    print(f"Locataire: {contrat.locataire.get_nom_complet()}")
    print(f"Loyer mensuel: {contrat.loyer_mensuel} F CFA")
    print()
    
    # Récupérer l'avance
    avance = contrat.avances_loyer.first()
    print(f"Avance ID: {avance.id}")
    print(f"Montant avance: {avance.montant_avance} F CFA")
    print(f"Mois couverts: {avance.nombre_mois_couverts}")
    print(f"Date début: {avance.mois_debut_couverture}")
    print(f"Date fin: {avance.mois_fin_couverture}")
    print(f"Montant restant: {avance.montant_restant} F CFA")
    print()
    
    # Test 1: Synchronisation des consommations manquantes
    print("1. SYNCHRONISATION DES CONSOMMATIONS MANQUANTES:")
    print("-" * 45)
    
    # Compter les consommations avant
    consommations_avant = ConsommationAvance.objects.filter(avance=avance).count()
    print(f"Consommations avant: {consommations_avant}")
    
    # Synchroniser
    ServiceGestionAvance.synchroniser_consommations_manquantes(contrat)
    
    # Compter les consommations après
    consommations_apres = ConsommationAvance.objects.filter(avance=avance).count()
    print(f"Consommations après: {consommations_apres}")
    print(f"Nouvelles consommations: {consommations_apres - consommations_avant}")
    
    # Afficher les consommations
    for consommation in ConsommationAvance.objects.filter(avance=avance):
        print(f"  - {consommation.mois_consomme.strftime('%B %Y')}: {consommation.montant_consomme} F CFA")
    
    print()
    
    # Test 2: Calcul du montant dû pour différents mois
    print("2. CALCUL DU MONTANT DU POUR DIFFERENTS MOIS:")
    print("-" * 50)
    
    # Tester plusieurs mois
    mois_tests = [
        avance.mois_debut_couverture,
        avance.mois_debut_couverture + relativedelta(months=1),
        avance.mois_debut_couverture + relativedelta(months=2),
        avance.mois_fin_couverture,
        avance.mois_fin_couverture + relativedelta(months=1)
    ]
    
    for mois in mois_tests:
        try:
            montant_du, montant_avance = ServiceGestionAvance.calculer_montant_du_mois(contrat, mois)
            print(f"  {mois.strftime('%B %Y')}:")
            print(f"    Montant dû: {montant_du} F CFA")
            print(f"    Avance utilisée: {montant_avance} F CFA")
            print(f"    Loyer mensuel: {contrat.loyer_mensuel} F CFA")
            print(f"    Charges: {contrat.charges_mensuelles or 0} F CFA")
            print()
        except Exception as e:
            print(f"  {mois.strftime('%B %Y')}: ERREUR - {str(e)}")
            print()
    
    # Test 3: Vérification de la cohérence des montants
    print("3. VERIFICATION DE LA COHERENCE DES MONTANTS:")
    print("-" * 50)
    
    # Recalculer le montant restant basé sur les consommations
    montant_consomme_calcule = sum(
        float(c.montant_consomme) for c in ConsommationAvance.objects.filter(avance=avance)
    )
    montant_restant_calcule = float(avance.montant_avance) - montant_consomme_calcule
    
    print(f"Montant avance original: {avance.montant_avance} F CFA")
    print(f"Montant consommé (enregistrements): {montant_consomme_calcule} F CFA")
    print(f"Montant restant (enregistrements): {montant_restant_calcule} F CFA")
    print(f"Montant restant (base de données): {avance.montant_restant} F CFA")
    print(f"Différence: {float(avance.montant_restant) - montant_restant_calcule} F CFA")
    
    if abs(float(avance.montant_restant) - montant_restant_calcule) < 0.01:
        print("OK - COHERENCE: Les montants sont coherents")
    else:
        print("ERREUR - INCOHERENCE: Les montants ne correspondent pas")
    
    print()
    
    # Test 4: Test de consommation d'avance pour un mois spécifique
    print("4. TEST DE CONSOMMATION POUR UN MOIS SPECIFIQUE:")
    print("-" * 55)
    
    # Prendre le premier mois de couverture
    mois_test = avance.mois_debut_couverture
    
    # Vérifier si ce mois a déjà été consommé
    consommation_existante = ConsommationAvance.objects.filter(
        avance=avance,
        mois_consomme=mois_test
    ).exists()
    
    print(f"Mois test: {mois_test.strftime('%B %Y')}")
    print(f"Consommation existante: {consommation_existante}")
    
    if not consommation_existante:
        # Tester la consommation
        avance_disponible, montant_avance = ServiceGestionAvance.consommer_avance_pour_mois(contrat, mois_test)
        print(f"Avance disponible: {avance_disponible}")
        print(f"Montant avance: {montant_avance} F CFA")
        
        # Vérifier la nouvelle consommation
        nouvelle_consommation = ConsommationAvance.objects.filter(
            avance=avance,
            mois_consomme=mois_test
        ).first()
        
        if nouvelle_consommation:
            print(f"Nouvelle consommation créée: {nouvelle_consommation.montant_consomme} F CFA")
        else:
            print("Aucune nouvelle consommation créée")
    else:
        print("Ce mois a déjà été consommé")
    
    print()
    
    # Test 5: Synchronisation globale
    print("5. SYNCHRONISATION GLOBALE:")
    print("-" * 30)
    
    resultat = ServiceGestionAvance.synchroniser_toutes_avances()
    print(f"Résultat: {resultat}")
    
    print()
    print("TEST D'INTEGRATION TERMINE")

if __name__ == "__main__":
    try:
        test_integration_avances_paiements()
    except Exception as e:
        print(f"ERREUR lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
