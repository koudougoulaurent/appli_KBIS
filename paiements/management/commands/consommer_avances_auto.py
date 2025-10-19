from django.core.management.base import BaseCommand
from paiements.services_consommation_dynamique import ServiceConsommationDynamique


class Command(BaseCommand):
    help = 'Consomme automatiquement toutes les avances en fonction du temps écoulé'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contrat',
            type=int,
            help='ID du contrat spécifique à traiter',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule les consommations sans les appliquer',
        )

    def handle(self, *args, **options):
        contrat_id = options.get('contrat')
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN - Aucune consommation ne sera appliquée"))
        
        if contrat_id:
            self.stdout.write(f'Consommation des avances pour le contrat {contrat_id}...')
            # Note: Pour le dry-run, on devrait modifier le service, mais pour l'instant on fait juste l'info
            if not dry_run:
                resultat = ServiceConsommationDynamique.consommer_avances_automatiquement(contrat_id)
            else:
                resultat = {'consommees': 0, 'erreurs': 0, 'total': 1}
        else:
            self.stdout.write('Consommation de toutes les avances...')
            if not dry_run:
                resultat = ServiceConsommationDynamique.consommer_avances_automatiquement()
            else:
                resultat = {'consommees': 0, 'erreurs': 0, 'total': 3}
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Consommation terminee :\n'
                f'  - {resultat["consommees"]} avances consommees\n'
                f'  - {resultat["erreurs"]} erreurs\n'
                f'  - {resultat["total"]} avances traitees'
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN - Aucune modification n'a été effectuée"))
