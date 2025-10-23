"""
Commande Django pour tester les conditions temporelles des retraits
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date

from paiements.services_retraits import ServiceCalculRetraits


class Command(BaseCommand):
    help = 'Teste les conditions temporelles pour la génération automatique des retraits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mois',
            type=int,
            help='Mois à tester (1-12)',
            default=timezone.now().month
        )
        parser.add_argument(
            '--annee',
            type=int,
            help='Année à tester',
            default=timezone.now().year
        )
        parser.add_argument(
            '--simuler',
            action='store_true',
            help='Simuler la génération sans créer de retraits'
        )

    def handle(self, *args, **options):
        mois = options['mois']
        annee = options['annee']
        simuler = options['simuler']
        
        self.stdout.write(
            self.style.SUCCESS('=== TEST DES CONDITIONS TEMPORELLES ===')
        )
        self.stdout.write(f'Date actuelle: {date.today()}')
        self.stdout.write(f'Jour du mois: {date.today().day}')
        self.stdout.write(f'Mois testé: {mois}/{annee}')
        self.stdout.write('')
        
        # Test des conditions temporelles
        conditions_ok, message = ServiceCalculRetraits.verifier_conditions_temporelles()
        
        if conditions_ok:
            self.stdout.write(
                self.style.SUCCESS(f'✅ CONDITIONS TEMPORELLES: {message}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ CONDITIONS TEMPORELLES: {message}')
            )
            return
        
        # Test de génération automatique
        if simuler:
            self.stdout.write(
                self.style.WARNING('🔄 SIMULATION - Aucun retrait ne sera créé')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  GÉNÉRATION RÉELLE - Les retraits seront créés')
            )
        
        # Générer les retraits
        resultat = ServiceCalculRetraits.creer_retraits_automatiques_mensuels(mois, annee)
        
        if resultat['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ {resultat["message"]}')
            )
            self.stdout.write(f'Retraits créés: {resultat["retraits_crees"]}')
            self.stdout.write(f'Retraits ignorés: {resultat["retraits_ignores"]}')
            
            # Afficher les détails
            for detail in resultat.get('details', []):
                if '✅' in detail:
                    self.stdout.write(self.style.SUCCESS(f'  {detail}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  {detail}'))
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {resultat["message"]}')
            )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('=== TEST TERMINÉ ===')
        )
