from django.core.management.base import BaseCommand
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from paiements.services_synchronisation_avances import ServiceSynchronisationAvances


class Command(BaseCommand):
    help = 'Corrige les liens entre les paiements d\'avance et les avances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la correction même si des erreurs sont détectées',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write('Correction des liens entre paiements et avances...')
        
        # Récupérer tous les paiements d'avance
        paiements_avance = Paiement.objects.filter(type_paiement='avance')
        
        corriges = 0
        erreurs = 0
        
        for paiement in paiements_avance:
            try:
                # Vérifier si une avance existe déjà pour ce paiement
                avance_existante = AvanceLoyer.objects.filter(paiement=paiement).first()
                
                if avance_existante:
                    self.stdout.write(f'Avance existe deja pour paiement {paiement.id}')
                    continue
                
                # Synchroniser l'avance
                avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
                
                if avance:
                    corriges += 1
                    self.stdout.write(f'OK - Lien corrige pour paiement {paiement.id} -> avance {avance.id}')
                else:
                    erreurs += 1
                    self.stdout.write(f'ERREUR - Impossible de corriger le lien pour paiement {paiement.id}')
                    
            except Exception as e:
                erreurs += 1
                self.stdout.write(f'ERREUR - Paiement {paiement.id}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Correction terminee :\n'
                f'  - {corriges} liens corriges\n'
                f'  - {erreurs} erreurs\n'
                f'  - {paiements_avance.count()} paiements traites'
            )
        )
