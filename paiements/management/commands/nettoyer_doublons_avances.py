from django.core.management.base import BaseCommand
from paiements.models_avance import AvanceLoyer
from django.db import transaction


class Command(BaseCommand):
    help = 'Nettoie les doublons d\'avances dans la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule le nettoyage sans supprimer les doublons',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN - Aucun doublon ne sera supprimé"))
        
        # Trouver les doublons basés sur contrat, montant et date
        doublons = []
        avances_traitees = set()
        
        for avance in AvanceLoyer.objects.all().order_by('id'):
            cle_doublon = (avance.contrat.id, float(avance.montant_avance), avance.date_avance)
            
            if cle_doublon in avances_traitees:
                doublons.append(avance)
            else:
                avances_traitees.add(cle_doublon)
        
        if not doublons:
            self.stdout.write(self.style.SUCCESS("Aucun doublon trouvé"))
            return
        
        self.stdout.write(f"Trouvé {len(doublons)} doublons d'avances")
        
        if dry_run:
            for avance in doublons:
                self.stdout.write(f"  - Avance {avance.id}: {avance.contrat.locataire.get_nom_complet()} - {avance.montant_avance} F CFA - {avance.date_avance}")
        else:
            # Supprimer les doublons (garder le plus ancien)
            supprimees = 0
            with transaction.atomic():
                for avance in doublons:
                    self.stdout.write(f"Suppression de l'avance {avance.id}")
                    avance.delete()
                    supprimees += 1
            
            self.stdout.write(
                self.style.SUCCESS(f"{supprimees} doublons supprimés avec succès")
            )
