"""
Commande Django pour nettoyer les types de paiement
Unifie tous les types d'avance en 'avance' uniquement
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from paiements.models import Paiement


class Command(BaseCommand):
    help = 'Nettoie les types de paiement pour unifier les avances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Nettoyage des types de paiement...')
        )
        
        # Trouver tous les paiements avec des types d'avance incorrects
        paiements_avance_loyer = Paiement.objects.filter(type_paiement='avance_loyer')
        paiements_depot_garantie = Paiement.objects.filter(type_paiement='depot_garantie')
        
        total_a_corriger = paiements_avance_loyer.count() + paiements_depot_garantie.count()
        
        if total_a_corriger == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucun paiement à corriger trouvé.')
            )
            return
        
        self.stdout.write(f'Paiements à corriger : {total_a_corriger}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode dry-run - Aucun changement ne sera appliqué')
            )
            
            for paiement in paiements_avance_loyer:
                self.stdout.write(
                    f'  - PAI-{paiement.id}: avance_loyer → avance'
                )
            
            for paiement in paiements_depot_garantie:
                self.stdout.write(
                    f'  - PAI-{paiement.id}: depot_garantie → caution'
                )
        else:
            # Appliquer les corrections
            with transaction.atomic():
                # Corriger avance_loyer → avance
                if paiements_avance_loyer.exists():
                    count_avance = paiements_avance_loyer.update(type_paiement='avance')
                    self.stdout.write(
                        self.style.SUCCESS(f'{count_avance} paiements avance_loyer → avance')
                    )
                
                # Corriger depot_garantie → caution
                if paiements_depot_garantie.exists():
                    count_caution = paiements_depot_garantie.update(type_paiement='caution')
                    self.stdout.write(
                        self.style.SUCCESS(f'{count_caution} paiements depot_garantie → caution')
                    )
        
        # Vérifier les types actuels
        self.stdout.write('\nStatistiques des types de paiement :')
        types_stats = Paiement.objects.values('type_paiement').annotate(
            count=Count('id')
        ).order_by('type_paiement')
        
        for stat in types_stats:
            self.stdout.write(f'  - {stat["type_paiement"]}: {stat["count"]} paiements')
        
        self.stdout.write(
            self.style.SUCCESS('\nNettoyage terminé !')
        )
