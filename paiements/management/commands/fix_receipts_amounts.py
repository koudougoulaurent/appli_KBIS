from django.core.management.base import BaseCommand
from paiements.models import Paiement
from django.db import transaction


class Command(BaseCommand):
    help = 'Corrige les montants des récépissés existants pour les avances'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN - Aucune modification ne sera effectuée'))
        
        # Récupérer tous les paiements d'avance
        paiements_avance = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide'
        ).select_related('contrat')
        
        self.stdout.write(f'Nombre de paiements d\'avance trouvés: {paiements_avance.count()}')
        
        corrections = 0
        
        with transaction.atomic():
            for paiement in paiements_avance:
                if paiement.contrat and paiement.contrat.avance_loyer:
                    try:
                        montant_avance_contrat = float(paiement.contrat.avance_loyer)
                        montant_paiement = float(paiement.montant)
                        
                        # Vérifier si les montants sont différents
                        if abs(montant_avance_contrat - montant_paiement) > 0.01:
                            self.stdout.write(
                                f'Paiement {paiement.id}: '
                                f'Montant paiement: {montant_paiement:,.0f} F CFA, '
                                f'Montant avance contrat: {montant_avance_contrat:,.0f} F CFA'
                            )
                            
                            if not dry_run:
                                # Mettre à jour le montant du paiement pour qu'il corresponde à l'avance
                                paiement.montant = montant_avance_contrat
                                paiement.save()
                                self.stdout.write(f'  -> Corrigé vers {montant_avance_contrat:,.0f} F CFA')
                            
                            corrections += 1
                        else:
                            self.stdout.write(f'Paiement {paiement.id}: Montants cohérents')
                            
                    except (ValueError, TypeError, AttributeError) as e:
                        self.stdout.write(
                            self.style.ERROR(f'Erreur pour le paiement {paiement.id}: {e}')
                        )
                else:
                    self.stdout.write(f'Paiement {paiement.id}: Pas de contrat ou avance_loyer manquant')
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY-RUN: {corrections} paiements seraient corrigés')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {corrections} paiements corrigés avec succès')
            )
