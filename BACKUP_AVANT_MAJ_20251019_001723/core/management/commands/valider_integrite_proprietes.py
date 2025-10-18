from django.core.management.base import BaseCommand
from django.db import transaction
from contrats.services import ProprieteValidationService
from proprietes.models import Propriete
from contrats.models import Contrat


class Command(BaseCommand):
    help = 'Valide et corrige l\'intégrité des propriétés et des contrats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--corriger',
            action='store_true',
            help='Corriger automatiquement les incohérences trouvées',
        )
        parser.add_argument(
            '--propriete',
            type=int,
            help='Valider une propriété spécifique par son ID',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher des informations détaillées',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Début de la validation de l\'intégrité des propriétés...')
        )

        if options['propriete']:
            # Valider une propriété spécifique
            try:
                propriete = Propriete.objects.get(pk=options['propriete'])
                self._valider_propriete(propriete, options['verbose'])
            except Propriete.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Propriété avec l\'ID {options["propriete"]} non trouvée')
                )
        else:
            # Valider toutes les propriétés
            self._valider_toutes_proprietes(options['corriger'], options['verbose'])

        self.stdout.write(
            self.style.SUCCESS('✅ Validation terminée')
        )

    def _valider_propriete(self, propriete, verbose=False):
        """Valide une propriété spécifique."""
        self.stdout.write(f'🔍 Validation de la propriété: {propriete.titre}')
        
        # Vérifier la disponibilité
        validation = ProprieteValidationService.verifier_disponibilite_propriete(propriete)
        
        if validation['disponible']:
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ {propriete.titre} est disponible et cohérente')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️ {propriete.titre} présente des incohérences:')
            )
            for message in validation['messages']:
                self.stdout.write(f'    - {message}')
            
            if verbose and validation['contrats_conflictuels']:
                self.stdout.write('    Contrats conflictuels:')
                for contrat in validation['contrats_conflictuels']:
                    self.stdout.write(f'      - {contrat.numero_contrat} ({contrat.date_debut} - {contrat.date_fin})')

    def _valider_toutes_proprietes(self, corriger=False, verbose=False):
        """Valide toutes les propriétés."""
        proprietes = Propriete.objects.all()
        total_proprietes = proprietes.count()
        
        self.stdout.write(f'📊 Validation de {total_proprietes} propriétés...')
        
        if corriger:
            self.stdout.write('🔧 Mode correction activé - les incohérences seront corrigées automatiquement')
        
        # Utiliser le service de validation
        rapport = ProprieteValidationService.valider_integrite_proprietes()
        
        # Afficher le rapport
        self.stdout.write(f'\n📋 Rapport de validation:')
        self.stdout.write(f'  - Propriétés vérifiées: {rapport["proprietes_verifiees"]}')
        self.stdout.write(f'  - Corrections effectuées: {rapport["corrections_effectuees"]}')
        
        if rapport['erreurs_trouvees']:
            self.stdout.write(f'  - Erreurs trouvées: {len(rapport["erreurs_trouvees"])}')
        
        # Afficher les corrections effectuées
        if rapport['corrections'] and verbose:
            self.stdout.write('\n🔧 Corrections effectuées:')
            for correction in rapport['corrections']:
                self.stdout.write(
                    f'  - {correction["propriete"]}: '
                    f'{correction["ancien_statut"]} → {correction["nouveau_statut"]}'
                )
                if correction['contrats_actifs']:
                    self.stdout.write(f'    Contrats actifs: {", ".join(correction["contrats_actifs"])}')
        
        # Afficher les erreurs
        if rapport['erreurs_trouvees'] and verbose:
            self.stdout.write('\n❌ Erreurs rencontrées:')
            for erreur in rapport['erreurs_trouvees']:
                self.stdout.write(f'  - {erreur["propriete"]}: {erreur["erreur"]}')
        
        # Statistiques finales
        proprietes_disponibles = Propriete.objects.filter(disponible=True).count()
        proprietes_louees = Propriete.objects.filter(disponible=False).count()
        
        self.stdout.write(f'\n📊 Statistiques finales:')
        self.stdout.write(f'  - Propriétés disponibles: {proprietes_disponibles}')
        self.stdout.write(f'  - Propriétés louées: {proprietes_louees}')
        
        # Vérification finale de cohérence
        contrats_actifs = Contrat.objects.filter(est_actif=True, est_resilie=False).count()
        self.stdout.write(f'  - Contrats actifs: {contrats_actifs}')
        
        if proprietes_louees != contrats_actifs:
            self.stdout.write(
                self.style.WARNING(
                    f'  ⚠️ ATTENTION: Incohérence détectée! '
                    f'Propriétés louées ({proprietes_louees}) ≠ Contrats actifs ({contrats_actifs})'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('  ✅ Cohérence vérifiée: Propriétés louées = Contrats actifs')
            )
