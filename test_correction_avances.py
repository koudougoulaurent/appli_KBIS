#!/usr/bin/env python
"""
Script de test pour diagnostiquer le problème de conversion des avances
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat

def diagnostiquer_conversion():
    """Diagnostique le problème de conversion des avances"""
    print("DIAGNOSTIC DE CONVERSION DES AVANCES")
    print("=" * 50)
    
    # 1. Vérifier les paiements d'avance existants
    print("\n1. PAIEMENTS D'AVANCE EXISTANTS:")
    paiements_avance = Paiement.objects.filter(
        type_paiement__in=['avance_loyer', 'avance'],
        statut='valide'
    )
    
    print(f"   Nombre total de paiements d'avance: {paiements_avance.count()}")
    
    for paiement in paiements_avance:
        print(f"   - ID: {paiement.id}")
        print(f"     Contrat: {paiement.contrat.id if paiement.contrat else 'N/A'}")
        print(f"     Montant: {paiement.montant} F CFA")
        print(f"     Date: {paiement.date_paiement}")
        print(f"     Type: {paiement.type_paiement}")
        print(f"     Statut: {paiement.statut}")
        print()
    
    # 2. Vérifier les avances de loyer existantes
    print("\n2. AVANCES DE LOYER EXISTANTES:")
    avances_loyer = AvanceLoyer.objects.all()
    
    print(f"   Nombre total d'avances de loyer: {avances_loyer.count()}")
    
    for avance in avances_loyer:
        print(f"   - ID: {avance.id}")
        print(f"     Contrat: {avance.contrat.id if avance.contrat else 'N/A'}")
        print(f"     Montant: {avance.montant_avance} F CFA")
        print(f"     Date: {avance.date_avance}")
        print(f"     Statut: {avance.statut}")
        print(f"     Mois couverts: {avance.nombre_mois_couverts}")
        print()
    
    # 3. Tester la conversion pour chaque contrat
    print("\n3. TEST DE CONVERSION PAR CONTRAT:")
    contrats_avec_avances = Contrat.objects.filter(
        paiements__type_paiement__in=['avance_loyer', 'avance'],
        paiements__statut='valide'
    ).distinct()
    
    print(f"   Nombre de contrats avec paiements d'avance: {contrats_avec_avances.count()}")
    
    for contrat in contrats_avec_avances:
        print(f"\n   CONTRAT {contrat.id}:")
        print(f"   - Locataire: {contrat.locataire.get_nom_complet() if contrat.locataire else 'N/A'}")
        print(f"   - Loyer mensuel: {contrat.loyer_mensuel} F CFA")
        
        # Paiements d'avance pour ce contrat
        paiements_contrat = Paiement.objects.filter(
            contrat=contrat,
            type_paiement__in=['avance_loyer', 'avance'],
            statut='valide'
        )
        
        print(f"   - Paiements d'avance: {paiements_contrat.count()}")
        
        for paiement in paiements_contrat:
            print(f"     * Paiement {paiement.id}: {paiement.montant} F CFA le {paiement.date_paiement}")
            
            # Vérifier si une avance existe déjà
            avance_existante = AvanceLoyer.objects.filter(
                contrat=paiement.contrat,
                montant_avance=paiement.montant,
                date_avance=paiement.date_paiement
            ).first()
            
            if avance_existante:
                print(f"       OK - AvanceLoyer existe deja (ID: {avance_existante.id})")
            else:
                print(f"       ERREUR - Aucune AvanceLoyer correspondante")
                
                # Tester la création
                try:
                    from paiements.services_avance import ServiceGestionAvance
                    
                    print(f"       🔄 Test de création d'avance...")
                    avance = ServiceGestionAvance.creer_avance_loyer(
                        contrat=paiement.contrat,
                        montant_avance=Decimal(str(paiement.montant)),
                        date_avance=paiement.date_paiement,
                        notes=f"Converti depuis paiement {paiement.id}"
                    )
                    print(f"       OK - Avance creee avec succes (ID: {avance.id})")
                    print(f"       - Mois couverts: {avance.nombre_mois_couverts}")
                    print(f"       - Montant restant: {avance.montant_restant} F CFA")
                    
                except Exception as e:
                    print(f"       ERREUR lors de la creation: {str(e)}")
        
        print()

def tester_conversion_complete():
    """Teste la conversion complète comme dans l'API"""
    print("\n4. TEST DE CONVERSION COMPLÈTE:")
    print("=" * 40)
    
    # Simuler la logique de l'API
    from paiements.services_avance import ServiceGestionAvance
    
    contrats_avec_avances = Contrat.objects.filter(
        paiements__type_paiement__in=['avance_loyer', 'avance'],
        paiements__statut='valide'
    ).distinct()
    
    total_avances_creees = 0
    
    for contrat in contrats_avec_avances:
        print(f"\n   CONTRAT {contrat.id}:")
        
        # Trouver tous les paiements d'avance de ce contrat
        paiements_avance = Paiement.objects.filter(
            contrat=contrat,
            type_paiement__in=['avance_loyer', 'avance'],
            statut='valide'
        )
        
        avances_creees_contrat = 0
        
        for paiement in paiements_avance:
            # Vérifier si un AvanceLoyer existe déjà pour ce paiement
            avance_existant = AvanceLoyer.objects.filter(
                contrat=paiement.contrat,
                montant_avance=paiement.montant,
                date_avance=paiement.date_paiement
            ).first()
            
            if not avance_existant:
                # Créer l'AvanceLoyer manquant
                try:
                    avance = ServiceGestionAvance.creer_avance_loyer(
                        contrat=paiement.contrat,
                        montant_avance=Decimal(str(paiement.montant)),
                        date_avance=paiement.date_paiement,
                        notes=f"Converti depuis paiement {paiement.id}"
                    )
                    # S'assurer que l'avance est active
                    avance.statut = 'active'
                    avance.save()
                    avances_creees_contrat += 1
                    print(f"     OK - Avance creee pour paiement {paiement.id}")
                except Exception as e:
                    print(f"     ERREUR creation AvanceLoyer pour paiement {paiement.id}: {str(e)}")
            else:
                print(f"     IGNORE - Avance existe deja pour paiement {paiement.id}")
        
        print(f"   Total avances créées pour ce contrat: {avances_creees_contrat}")
        total_avances_creees += avances_creees_contrat
    
    print(f"\nRESULTAT FINAL: {total_avances_creees} avances creees au total")

if __name__ == "__main__":
    try:
        diagnostiquer_conversion()
        tester_conversion_complete()
    except Exception as e:
        print(f"ERREUR lors du diagnostic: {str(e)}")
        import traceback
        traceback.print_exc()