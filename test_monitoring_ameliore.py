#!/usr/bin/env python
"""
Script de test pour le système de monitoring amélioré des avances
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.services_monitoring_avance import ServiceMonitoringAvance
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat

def test_monitoring_complet():
    """Test complet du système de monitoring"""
    print("TEST COMPLET DU SYSTEME DE MONITORING DES AVANCES")
    print("=" * 60)
    
    # 1. Test du rapport de progression
    print("\n1. RAPPORT DE PROGRESSION:")
    rapport = ServiceMonitoringAvance.generer_rapport_progression()
    
    if 'erreur' in rapport:
        print(f"   ERREUR: {rapport['erreur']}")
    else:
        print(f"   Total avances: {rapport['total_avances']}")
        print(f"   Avances actives: {rapport['avances_actives']}")
        print(f"   Avances epuisees: {rapport['avances_epuisees']}")
        print(f"   Avances critiques: {rapport['avances_critiques']}")
        print(f"   Montant total: {rapport['montant_total_avances']} F CFA")
        print(f"   Montant restant: {rapport['montant_restant_total']} F CFA")
        print(f"   Progression moyenne: {rapport['progression_moyenne']}%")
        print(f"   Pourcentage consomme: {rapport['pourcentage_consomme']}%")
    
    # 2. Test de la détection des avances critiques
    print("\n2. DETECTION DES AVANCES CRITIQUES:")
    avances_critiques = ServiceMonitoringAvance.detecter_avances_critiques()
    
    if avances_critiques:
        print(f"   {len(avances_critiques)} avances critiques detectees:")
        for alerte in avances_critiques:
            print(f"   - {alerte['message']}")
            print(f"     Type: {alerte['type_alerte']}")
            print(f"     Progression: {alerte['progression']}%")
    else:
        print("   Aucune avance critique detectee")
    
    # 3. Test de l'analyse de progression pour chaque avance
    print("\n3. ANALYSE DE PROGRESSION PAR AVANCE:")
    avances = AvanceLoyer.objects.all()
    
    for avance in avances:
        print(f"\n   Avance {avance.id} (Contrat {avance.contrat_id}):")
        progression = ServiceMonitoringAvance.analyser_progression_avance(avance)
        
        if 'erreur' in progression:
            print(f"     ERREUR: {progression['erreur']}")
        else:
            print(f"     Progression: {progression['progression']}%")
            print(f"     Mois consommes: {progression['mois_consommes']}")
            print(f"     Mois ecoules: {progression['mois_ecoules']}")
            print(f"     Mois restants estimes: {progression['mois_restants_estimes']}")
            print(f"     Montant reel consomme: {progression['montant_reel_consomme']} F CFA")
            print(f"     Pourcentage reel: {progression['pourcentage_reel']}%")
            print(f"     Statut progression: {progression['statut_progression']}")
            if progression['date_expiration_estimee']:
                print(f"     Date expiration estimee: {progression['date_expiration_estimee']}")
    
    # 4. Test de la synchronisation
    print("\n4. TEST DE SYNCHRONISATION:")
    resultat_sync = ServiceMonitoringAvance.synchroniser_consommations()
    
    if resultat_sync.get('success', False):
        print(f"   Synchronisation reussie: {resultat_sync['message']}")
        print(f"   Total synchronise: {resultat_sync['total_synchronise']}")
    else:
        print(f"   ERREUR synchronisation: {resultat_sync.get('erreur', 'Erreur inconnue')}")
    
    # 5. Test de l'envoi d'alertes
    print("\n5. TEST D'ENVOI D'ALERTES:")
    resultat_alertes = ServiceMonitoringAvance.envoyer_alertes()
    
    if resultat_alertes.get('success', False):
        print(f"   Alertes envoyees: {resultat_alertes['message']}")
        print(f"   Nombre d'alertes: {resultat_alertes['alertes_envoyees']}")
    else:
        print(f"   ERREUR envoi alertes: {resultat_alertes.get('erreur', 'Erreur inconnue')}")
    
    # 6. Résumé final
    print("\n6. RESUME FINAL:")
    print(f"   - {rapport.get('total_avances', 0)} avances au total")
    print(f"   - {rapport.get('avances_actives', 0)} avances actives")
    print(f"   - {rapport.get('avances_critiques', 0)} avances critiques")
    print(f"   - {len(avances_critiques)} alertes generees")
    print(f"   - Montant total: {rapport.get('montant_total_avances', 0)} F CFA")
    print(f"   - Montant restant: {rapport.get('montant_restant_total', 0)} F CFA")
    
    print("\nOK - Test du monitoring termine avec succes!")

if __name__ == "__main__":
    try:
        test_monitoring_complet()
    except Exception as e:
        print(f"ERREUR lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
