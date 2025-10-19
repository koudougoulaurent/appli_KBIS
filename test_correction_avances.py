#!/usr/bin/env python
"""
Script simple pour corriger les avances qui ont des mois futurs marqués comme consommés.
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from datetime import date
from dateutil.relativedelta import relativedelta
from paiements.models_avance import AvanceLoyer, ConsommationAvance


def corriger_avances_futures(dry_run=True):
    """Corrige les avances qui ont des mois futurs marqués comme consommés."""
    
    if dry_run:
        print('🔍 Mode DRY-RUN - Aucune modification ne sera effectuée')
    
    aujourd_hui = date.today()
    mois_actuel = aujourd_hui.replace(day=1)
    
    print(f'📅 Mois actuel: {mois_actuel}')
    
    # Récupérer toutes les avances actives
    avances = AvanceLoyer.objects.filter(statut='active')
    
    total_avances = avances.count()
    avances_corrigees = 0
    consommations_supprimees = 0
    
    print(f'🔍 Analyse de {total_avances} avances actives...')
    
    for avance in avances:
        if not avance.mois_debut_couverture:
            continue
        
        # Récupérer toutes les consommations de cette avance
        consommations = ConsommationAvance.objects.filter(avance=avance).order_by('mois_consomme')
        
        consommations_futures = []
        for consommation in consommations:
            if consommation.mois_consomme >= mois_actuel:
                consommations_futures.append(consommation)
        
        if consommations_futures:
            print(f'\n⚠️  Avance {avance.id} (Contrat {avance.contrat.id}):')
            print(f'   Période: {avance.mois_debut_couverture} - {avance.mois_fin_couverture}')
            print(f'   Mois couverts: {avance.nombre_mois_couverts}')
            
            for consommation in consommations_futures:
                print(f'   ❌ Consommation future: {consommation.mois_consomme} (devrait être supprimée)')
            
            if not dry_run:
                # Supprimer les consommations futures
                for consommation in consommations_futures:
                    consommation.delete()
                    consommations_supprimees += 1
                
                # Recalculer le montant restant
                montant_consomme = sum(
                    c.montant_consomme for c in ConsommationAvance.objects.filter(avance=avance)
                )
                avance.montant_restant = avance.montant_avance - montant_consomme
                avance.save()
                
                print(f'   ✅ {len(consommations_futures)} consommations futures supprimées')
                print(f'   ✅ Montant restant recalculé: {avance.montant_restant:,.0f} F CFA')
            
            avances_corrigees += 1
    
    # Résumé
    print(f'\n📊 RÉSUMÉ:')
    print(f'   Avances analysées: {total_avances}')
    print(f'   Avances avec problèmes: {avances_corrigees}')
    
    if not dry_run:
        print(f'   Consommations futures supprimées: {consommations_supprimees}')
        print('✅ Correction terminée avec succès')
    else:
        print('🔍 Mode DRY-RUN - Aucune modification effectuée')
        print('   Pour appliquer les corrections, relancez avec dry_run=False')


if __name__ == '__main__':
    # Test en mode dry-run d'abord
    print('=== CORRECTION DES AVANCES FUTURES ===')
    corriger_avances_futures(dry_run=True)
    
    # Demander confirmation pour la correction réelle
    print('\n' + '='*50)
    response = input('Voulez-vous appliquer les corrections ? (oui/non): ')
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        print('\n=== APPLICATION DES CORRECTIONS ===')
        corriger_avances_futures(dry_run=False)
    else:
        print('❌ Correction annulée')
