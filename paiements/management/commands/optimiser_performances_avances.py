"""
Commande pour optimiser les performances des requêtes sur les avances
"""
from django.core.management.base import BaseCommand
from paiements.optimisation_performance import optimiser_requetes_avances


class Command(BaseCommand):
    help = 'Optimise les performances des requêtes sur les avances en ajoutant des index'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('OPTIMISATION DES PERFORMANCES - AVANCES'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))
        
        self.stdout.write('Ajout des index sur les tables...\n')
        
        try:
            optimiser_requetes_avances()
            self.stdout.write(self.style.SUCCESS('\n✓ Optimisation terminée avec succès'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erreur lors de l\'optimisation: {e}'))
            import traceback
            traceback.print_exc()
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}\n'))
