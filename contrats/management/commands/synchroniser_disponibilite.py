"""
Commande Django pour synchroniser la disponibilité des propriétés.
"""
from django.core.management.base import BaseCommand
from contrats.utils import synchroniser_disponibilite_proprietes


class Command(BaseCommand):
    help = 'Synchronise la disponibilité des propriétés basée sur les contrats actifs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails de la synchronisation',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 Début de la synchronisation de la disponibilité des propriétés...')
        )
        
        try:
            synchroniser_disponibilite_proprietes()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Synchronisation terminée avec succès!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la synchronisation: {str(e)}')
            )
            raise
