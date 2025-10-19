from django.core.management.base import BaseCommand
from paiements.services_synchronisation_avances import ServiceSynchronisationAvances


class Command(BaseCommand):
    help = 'Synchronise parfaitement toutes les avances avec leurs paiements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verifier',
            action='store_true',
            help='Vérifier seulement la cohérence sans synchroniser',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la synchronisation même si des erreurs sont détectées',
        )

    def handle(self, *args, **options):
        verifier_seulement = options['verifier']
        force = options['force']
        
        if verifier_seulement:
            self.stdout.write('Verification de la coherence des avances...')
            incohérences = ServiceSynchronisationAvances.verifier_coherence_avances()
            
            if not incohérences:
                self.stdout.write(self.style.SUCCESS('Toutes les avances sont coherentes !'))
            else:
                self.stdout.write(self.style.WARNING(f'{len(incohérences)} incohérences détectées :'))
                for incohérence in incohérences:
                    self.stdout.write(f'  - Paiement {incohérence["paiement_id"]}: {incohérence["message"]}')
                    if incohérence['type'] == 'montant_incoherent':
                        self.stdout.write(f'    Montant paiement: {incohérence["montant_paiement"]:,.0f} F CFA')
                        self.stdout.write(f'    Montant avance: {incohérence["montant_avance"]:,.0f} F CFA')
                    elif incohérence['type'] == 'mois_incoherents':
                        self.stdout.write(f'    Mois attendu: {incohérence["mois_attendu"]}')
                        self.stdout.write(f'    Mois actuel: {incohérence["mois_actuel"]}')
        else:
            self.stdout.write('Synchronisation des avances avec les paiements...')
            
            # Vérifier d'abord la cohérence
            incohérences = ServiceSynchronisationAvances.verifier_coherence_avances()
            
            if incohérences and not force:
                self.stdout.write(self.style.WARNING(f'{len(incohérences)} incohérences détectées.'))
                self.stdout.write('Utilisez --force pour forcer la synchronisation.')
                return
            
            # Effectuer la synchronisation
            resultat = ServiceSynchronisationAvances.synchroniser_toutes_avances()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Synchronisation terminee :\n'
                    f'  - {resultat["synchronisees"]} avances synchronisees\n'
                    f'  - {resultat["erreurs"]} erreurs\n'
                    f'  - {resultat["total"]} paiements traites'
                )
            )
            
            if resultat['erreurs'] > 0:
                self.stdout.write(
                    self.style.WARNING('Des erreurs ont ete rencontrees. Verifiez les logs.')
                )
