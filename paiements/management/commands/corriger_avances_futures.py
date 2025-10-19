"""
Commande pour corriger les avances qui ont des mois futurs marqués comme consommés.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from paiements.models_avance import AvanceLoyer, ConsommationAvance


class Command(BaseCommand):
    help = 'Corrige les avances qui ont des mois futurs marqués comme consommés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait corrigé sans faire les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Mode DRY-RUN - Aucune modification ne sera effectuée'))
        
        aujourd_hui = date.today()
        mois_actuel = aujourd_hui.replace(day=1)
        
        self.stdout.write(f'📅 Mois actuel: {mois_actuel}')
        
        # Récupérer toutes les avances actives
        avances = AvanceLoyer.objects.filter(statut='active')
        
        total_avances = avances.count()
        avances_corrigees = 0
        consommations_supprimees = 0
        
        self.stdout.write(f'🔍 Analyse de {total_avances} avances actives...')
        
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
                self.stdout.write(f'\n⚠️  Avance {avance.id} (Contrat {avance.contrat.id}):')
                self.stdout.write(f'   Période: {avance.mois_debut_couverture} - {avance.mois_fin_couverture}')
                self.stdout.write(f'   Mois couverts: {avance.nombre_mois_couverts}')
                
                for consommation in consommations_futures:
                    self.stdout.write(f'   ❌ Consommation future: {consommation.mois_consomme} (devrait être supprimée)')
                
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
                    
                    self.stdout.write(f'   ✅ {len(consommations_futures)} consommations futures supprimées')
                    self.stdout.write(f'   ✅ Montant restant recalculé: {avance.montant_restant:,.0f} F CFA')
                
                avances_corrigees += 1
        
        # Résumé
        self.stdout.write(f'\n📊 RÉSUMÉ:')
        self.stdout.write(f'   Avances analysées: {total_avances}')
        self.stdout.write(f'   Avances avec problèmes: {avances_corrigees}')
        
        if not dry_run:
            self.stdout.write(f'   Consommations futures supprimées: {consommations_supprimees}')
            self.stdout.write(self.style.SUCCESS('✅ Correction terminée avec succès'))
        else:
            self.stdout.write(self.style.WARNING('🔍 Mode DRY-RUN - Aucune modification effectuée'))
            self.stdout.write('   Pour appliquer les corrections, relancez sans --dry-run')
